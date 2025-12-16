export type TagType = '' | 'success' | 'warning' | 'danger' | 'info'

export const STOCK_TXN_TYPE_OPTIONS: Array<{ value: string; label: string; tagType: TagType }> = [
  { value: 'IN', label: '入库', tagType: 'success' },
  { value: 'OUT', label: '领用', tagType: 'warning' },
]

export const STOCK_TXN_STATUS_OPTIONS: Array<{ value: string; label: string; tagType: TagType }> = [
  { value: 'PENDING', label: '待审核', tagType: 'warning' },
  { value: 'APPROVED', label: '已通过', tagType: 'success' },
  { value: 'REJECTED', label: '已拒绝', tagType: 'danger' },
]

const TYPE_META = new Map(STOCK_TXN_TYPE_OPTIONS.map((item) => [item.value, item]))
const STATUS_META = new Map(STOCK_TXN_STATUS_OPTIONS.map((item) => [item.value, item]))

export function getStockTxnTypeLabel(value: string): string {
  return TYPE_META.get(value)?.label ?? value
}

export function getStockTxnTypeTagType(value: string): TagType {
  return TYPE_META.get(value)?.tagType ?? 'info'
}

export function getStockTxnStatusLabel(value: string): string {
  return STATUS_META.get(value)?.label ?? value
}

export function getStockTxnStatusTagType(value: string): TagType {
  return STATUS_META.get(value)?.tagType ?? 'info'
}

