export type TagType = '' | 'success' | 'warning' | 'danger' | 'info'

export const BORROW_REQUEST_STATUS_OPTIONS: Array<{ value: string; label: string; tagType: TagType }> = [
  { value: 'REQUESTED', label: '待审批', tagType: 'warning' },
  { value: 'APPROVED', label: '已通过', tagType: 'success' },
  { value: 'REJECTED', label: '已拒绝', tagType: 'danger' },
  { value: 'OUT', label: '已出库', tagType: 'warning' },
  { value: 'CLOSED', label: '已关闭', tagType: 'info' },
]

export const BORROW_ITEM_STATUS_OPTIONS: Array<{ value: string; label: string; tagType: TagType }> = [
  { value: 'PENDING', label: '待出库', tagType: 'warning' },
  { value: 'OUT', label: '已出库', tagType: 'success' },
  { value: 'RETURN_PENDING', label: '待验收', tagType: 'info' },
  { value: 'RETURN_ACCEPTED', label: '已验收', tagType: 'success' },
  { value: 'RETURN_REJECTED', label: '拒收', tagType: 'danger' },
]

const REQUEST_META = new Map(BORROW_REQUEST_STATUS_OPTIONS.map((item) => [item.value, item]))
const ITEM_META = new Map(BORROW_ITEM_STATUS_OPTIONS.map((item) => [item.value, item]))

export function getBorrowRequestStatusLabel(status: string): string {
  return REQUEST_META.get(status)?.label ?? status
}

export function getBorrowRequestStatusTagType(status: string): TagType {
  return REQUEST_META.get(status)?.tagType ?? 'info'
}

export function getBorrowItemStatusLabel(status: string): string {
  return ITEM_META.get(status)?.label ?? status
}

export function getBorrowItemStatusTagType(status: string): TagType {
  return ITEM_META.get(status)?.tagType ?? 'info'
}

