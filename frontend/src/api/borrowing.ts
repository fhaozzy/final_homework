import { http } from './http'
import type { Paginated } from './types'

export interface EquipmentBrief {
  id: number
  code: string
  name: string
  status: string
  category_id: number
  location: string
  usable: boolean
}

export interface BorrowItem {
  id: number
  item_type: 'EQUIPMENT' | 'CONSUMABLE'
  equipment: EquipmentBrief | null
  equipment_id: number | null
  qty: number
  status: string
  out_at: string | null
  due_at: string | null
  return_submitted_at: string | null
  return_checked_at: string | null
  created_at: string
  updated_at: string
}

export interface BorrowApproval {
  id: number
  decision: 'APPROVED' | 'REJECTED'
  comment: string
  decided_at: string
  approver: number
  approver_username: string
  created_at: string
  updated_at: string
}

export interface BorrowRequest {
  id: number
  type: 'EQUIPMENT' | 'CONSUMABLE'
  status: string
  purpose: string
  expected_return_date: string | null
  submitted_at: string | null
  approved_at: string | null
  rejected_at: string | null
  remark: string
  applicant: number
  applicant_username: string
  approver: number | null
  approver_username: string
  created_at: string
  updated_at: string
  items: BorrowItem[]
  approval: BorrowApproval | null
}

export function listBorrowRequests(params: { page?: number } = {}): Promise<Paginated<BorrowRequest>> {
  return http.get<Paginated<BorrowRequest>>('/borrow/requests/', { params }).then((r) => r.data)
}

export function fetchBorrowRequest(id: number): Promise<BorrowRequest> {
  return http.get<BorrowRequest>(`/borrow/requests/${id}/`).then((r) => r.data)
}

export function createBorrowRequest(payload: {
  purpose?: string
  expected_return_date?: string | null
  remark?: string
  items: Array<{ equipment_id: number }>
}): Promise<BorrowRequest> {
  return http.post<BorrowRequest>('/borrow/requests/', payload).then((r) => r.data)
}

export function approveBorrowRequest(id: number, payload: { comment?: string } = {}): Promise<BorrowRequest> {
  return http.post<BorrowRequest>(`/borrow/requests/${id}/approve/`, payload).then((r) => r.data)
}

export function rejectBorrowRequest(id: number, payload: { comment?: string } = {}): Promise<BorrowRequest> {
  return http.post<BorrowRequest>(`/borrow/requests/${id}/reject/`, payload).then((r) => r.data)
}

export function checkoutBorrowRequest(id: number): Promise<BorrowRequest> {
  return http.post<BorrowRequest>(`/borrow/requests/${id}/checkout/`).then((r) => r.data)
}

export type ReturnCondition = 'GOOD' | 'DAMAGED' | 'LOST'

export function submitReturnRequest(
  id: number,
  payload: {
    items?: Array<{ borrow_item_id: number }>
  } = {},
): Promise<BorrowRequest> {
  return http.post<BorrowRequest>(`/borrow/requests/${id}/submit-return/`, payload).then((r) => r.data)
}

export function returnBorrowRequest(
  id: number,
  payload: {
    items?: Array<{ borrow_item_id: number; condition?: ReturnCondition; fee?: number | string; remark?: string }>
  } = {},
): Promise<BorrowRequest> {
  return http.post<BorrowRequest>(`/borrow/requests/${id}/return/`, payload).then((r) => r.data)
}

