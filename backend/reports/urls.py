from django.urls import path

from reports.views import BorrowTopReportView, ConsumableMonthlyReportView, EquipmentUtilizationReportView

urlpatterns = [
    path("borrow-top/", BorrowTopReportView.as_view(), name="report-borrow-top"),
    path("equipment-utilization/", EquipmentUtilizationReportView.as_view(), name="report-equipment-utilization"),
    path("consumable-monthly/", ConsumableMonthlyReportView.as_view(), name="report-consumable-monthly"),
]

