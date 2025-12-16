import { http } from './http'
import type { Paginated } from './types'

export type StockTxnType = 'IN' | 'OUT'
export type StockTxnStatus = 'PENDING' | 'APPROVED' | 'REJECTED'

export interface StockTxn {
  id: number
  consumable_id: number
  consumable_code: string
  consumable_name: string
  type: StockTxnType
  status: StockTxnStatus
  qty: number
  remark: string
  performed_by: number
  performed_by_username: string
  reviewed_by: number | null
  reviewed_by_username: string
  decided_at: string | null
  created_at: string
  updated_at: string
}

export function listStockTxns(params: { page?: number } = {}): Promise<Paginated<StockTxn>> {
  return http.get<Paginated<StockTxn>>('/stock/', { params }).then((r) => r.data)
}

export function stockIn(payload: { consumable_id: number; qty: number; remark?: string }): Promise<StockTxn> {
  return http.post<StockTxn>('/stock/in/', payload).then((r) => r.data)
}

export function stockOut(payload: { consumable_id: number; qty: number; remark?: string }): Promise<StockTxn> {
  return http.post<StockTxn>('/stock/out/', payload).then((r) => r.data)
}

export function approveStockTxn(id: number): Promise<StockTxn> {
  return http.post<StockTxn>(`/stock/${id}/approve/`).then((r) => r.data)
}

export function rejectStockTxn(id: number): Promise<StockTxn> {
  return http.post<StockTxn>(`/stock/${id}/reject/`).then((r) => r.data)
}

