import datetime
from collections import defaultdict

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminUser
from borrowing.models import BorrowItem
from inventory.models import Equipment, StockTxn, StockTxnStatus, StockTxnType


def _parse_date(value: str, field: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError({field: "Invalid date, expected YYYY-MM-DD."}) from exc


def _parse_positive_int(value: str | None, field: str, default: int, max_value: int | None = None) -> int:
    if value is None or value == "":
        result = default
    else:
        try:
            result = int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError({field: "Invalid integer."}) from exc

    if result <= 0:
        raise ValidationError({field: "Must be a positive integer."})
    if max_value is not None and result > max_value:
        raise ValidationError({field: f"Must be <= {max_value}."})
    return result


def _date_range_to_utc_datetimes(start_date: datetime.date, end_date: datetime.date) -> tuple[datetime.datetime, datetime.datetime]:
    tz = timezone.get_current_timezone()
    start_dt = datetime.datetime.combine(start_date, datetime.time.min, tzinfo=tz)
    end_exclusive_dt = datetime.datetime.combine(end_date + datetime.timedelta(days=1), datetime.time.min, tzinfo=tz)
    return start_dt.astimezone(datetime.timezone.utc), end_exclusive_dt.astimezone(datetime.timezone.utc)


class BorrowTopReportView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        limit = _parse_positive_int(request.query_params.get("limit"), "limit", default=10, max_value=200)
        start_param = request.query_params.get("start")
        end_param = request.query_params.get("end")

        qs = BorrowItem.objects.filter(
            item_type=BorrowItem.ItemType.EQUIPMENT,
            equipment__isnull=False,
            out_at__isnull=False,
        )

        start_date = None
        end_date = None
        if start_param or end_param:
            if not start_param or not end_param:
                raise ValidationError({"range": "Both start and end are required when filtering by range."})
            start_date = _parse_date(start_param, "start")
            end_date = _parse_date(end_param, "end")
            if start_date > end_date:
                raise ValidationError({"range": "start must be <= end."})
            start_dt, end_exclusive_dt = _date_range_to_utc_datetimes(start_date, end_date)
            qs = qs.filter(out_at__gte=start_dt, out_at__lt=end_exclusive_dt)

        rows = list(
            qs.values("equipment_id", "equipment__code", "equipment__name")
            .annotate(borrow_count=Count("id"))
            .order_by("-borrow_count", "equipment_id")[:limit]
        )

        items = [
            {
                "equipment_id": row["equipment_id"],
                "equipment_code": row["equipment__code"],
                "equipment_name": row["equipment__name"],
                "borrow_count": row["borrow_count"],
            }
            for row in rows
        ]

        return Response(
            {
                "limit": limit,
                "range": {"start": start_date, "end": end_date},
                "items": items,
            }
        )


class EquipmentUtilizationReportView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        start_param = request.query_params.get("start")
        end_param = request.query_params.get("end")
        if not start_param or not end_param:
            raise ValidationError({"range": "start and end are required."})

        start_date = _parse_date(start_param, "start")
        end_date = _parse_date(end_param, "end")
        if start_date > end_date:
            raise ValidationError({"range": "start must be <= end."})

        range_days = (end_date - start_date).days + 1
        start_dt, end_exclusive_dt = _date_range_to_utc_datetimes(start_date, end_date)

        limit = _parse_positive_int(request.query_params.get("limit"), "limit", default=200, max_value=5000)
        include_zero = request.query_params.get("include_zero", "1") != "0"

        overlapping_items = (
            BorrowItem.objects.only("equipment_id", "out_at", "return_checked_at")
            .filter(
                item_type=BorrowItem.ItemType.EQUIPMENT,
                equipment__isnull=False,
                out_at__isnull=False,
                out_at__lt=end_exclusive_dt,
            )
            .filter(
                # return_checked_at is NULL when still borrowed
                # overlap condition: return_dt >= start_dt
                # (NULL treated as ongoing)
                Q(return_checked_at__gte=start_dt) | Q(return_checked_at__isnull=True)
            )
        )

        intervals_by_equipment: dict[int, list[tuple[datetime.date, datetime.date]]] = defaultdict(list)
        for item in overlapping_items:
            out_date = timezone.localtime(item.out_at).date()
            return_date = timezone.localtime(item.return_checked_at).date() if item.return_checked_at else end_date

            interval_start = max(out_date, start_date)
            interval_end = min(return_date, end_date)
            if interval_start <= interval_end:
                intervals_by_equipment[item.equipment_id].append((interval_start, interval_end))

        def merged_days(intervals: list[tuple[datetime.date, datetime.date]]) -> int:
            if not intervals:
                return 0
            intervals.sort(key=lambda x: (x[0], x[1]))
            total = 0
            cur_start, cur_end = intervals[0]
            for start, end in intervals[1:]:
                if start <= (cur_end + datetime.timedelta(days=1)):
                    if end > cur_end:
                        cur_end = end
                    continue
                total += (cur_end - cur_start).days + 1
                cur_start, cur_end = start, end
            total += (cur_end - cur_start).days + 1
            return total

        borrow_days_by_equipment: dict[int, int] = {
            equipment_id: merged_days(intervals) for equipment_id, intervals in intervals_by_equipment.items()
        }

        equipment_qs = Equipment.objects.only("id", "code", "name").order_by("id")
        items = []
        for equipment in equipment_qs:
            borrowed_days = borrow_days_by_equipment.get(equipment.id, 0)
            if borrowed_days == 0 and not include_zero:
                continue

            utilization = borrowed_days / range_days if range_days else 0
            items.append(
                {
                    "equipment_id": equipment.id,
                    "equipment_code": equipment.code,
                    "equipment_name": equipment.name,
                    "borrowed_days": borrowed_days,
                    "range_days": range_days,
                    "utilization_rate": round(utilization, 6),
                }
            )

        items.sort(key=lambda x: (-x["utilization_rate"], -x["borrowed_days"], x["equipment_id"]))
        items = items[:limit]

        return Response(
            {
                "range": {"start": start_date, "end": end_date, "range_days": range_days},
                "items": items,
            }
        )


class ConsumableMonthlyReportView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        year_param = request.query_params.get("year")
        if year_param:
            try:
                year = int(year_param)
            except (TypeError, ValueError) as exc:
                raise ValidationError({"year": "Invalid year."}) from exc
        else:
            year = timezone.now().year

        qs = StockTxn.objects.filter(type=StockTxnType.OUT, status=StockTxnStatus.APPROVED, decided_at__isnull=False)

        consumable_id = request.query_params.get("consumable_id")
        if consumable_id:
            try:
                consumable_id_int = int(consumable_id)
            except (TypeError, ValueError) as exc:
                raise ValidationError({"consumable_id": "Invalid integer."}) from exc
            qs = qs.filter(consumable_id=consumable_id_int)

        tz = timezone.get_current_timezone()
        year_start = datetime.datetime(year, 1, 1, 0, 0, 0, tzinfo=tz).astimezone(datetime.timezone.utc)
        year_end = datetime.datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=tz).astimezone(datetime.timezone.utc)

        qty_by_month = {month: 0 for month in range(1, 13)}
        for txn in qs.only("qty", "decided_at").filter(decided_at__gte=year_start, decided_at__lt=year_end):
            decided_local = timezone.localtime(txn.decided_at, timezone=tz)
            qty_by_month[decided_local.month] += int(txn.qty)
        items = [
            {"month": f"{year}-{month:02d}", "qty": qty_by_month.get(month, 0)}
            for month in range(1, 13)
        ]

        return Response(
            {
                "year": year,
                "items": items,
            }
        )
