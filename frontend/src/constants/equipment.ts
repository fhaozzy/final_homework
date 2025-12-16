export type TagType = '' | 'success' | 'warning' | 'danger' | 'info'

export const EQUIPMENT_STATUS_OPTIONS: Array<{ value: string; label: string; tagType: TagType }> = [
  { value: 'AVAILABLE', label: '可用', tagType: 'success' },
  { value: 'RESERVED', label: '已预留', tagType: 'warning' },
  { value: 'BORROWED', label: '已借出', tagType: 'warning' },
  { value: 'OUT', label: '已出库(旧)', tagType: 'warning' },
  { value: 'RETURN_PENDING', label: '待验收', tagType: 'info' },
  { value: 'MAINTENANCE', label: '维修中', tagType: 'danger' },
  { value: 'DISCARDED', label: '已报废', tagType: 'info' },
]

const STATUS_META = new Map(EQUIPMENT_STATUS_OPTIONS.map((item) => [item.value, item]))

export function getEquipmentStatusLabel(status: string): string {
  return STATUS_META.get(status)?.label ?? status
}

export function getEquipmentStatusTagType(status: string): TagType {
  return STATUS_META.get(status)?.tagType ?? 'info'
}

