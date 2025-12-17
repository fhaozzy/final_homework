export type TagType = '' | 'success' | 'warning' | 'danger' | 'info'

export const MAINTENANCE_STATUS_OPTIONS: Array<{ value: string; label: string; tagType: TagType }> = [
  { value: 'OPEN', label: '待处理', tagType: 'warning' },
  { value: 'IN_PROGRESS', label: '处理中', tagType: 'warning' },
  { value: 'DONE', label: '已完成', tagType: 'success' },
]

const STATUS_META = new Map(MAINTENANCE_STATUS_OPTIONS.map((item) => [item.value, item]))

export function getMaintenanceStatusLabel(status: string): string {
  return STATUS_META.get(status)?.label ?? status
}

export function getMaintenanceStatusTagType(status: string): TagType {
  return STATUS_META.get(status)?.tagType ?? 'info'
}

