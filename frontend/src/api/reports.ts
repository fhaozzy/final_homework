import { http } from './http'

export interface BorrowTopItem {
  equipment_id: number
  equipment_code: string
  equipment_name: string
  borrow_count: number
}

export interface BorrowTopReport {
  limit: number
  range: { start: string | null; end: string | null }
  items: BorrowTopItem[]
}

export function fetchBorrowTopReport(params: {
  limit?: number
  start?: string
  end?: string
} = {}): Promise<BorrowTopReport> {
  return http.get<BorrowTopReport>('/reports/borrow-top/', { params }).then((r) => r.data)
}

export interface EquipmentUtilizationItem {
  equipment_id: number
  equipment_code: string
  equipment_name: string
  borrowed_days: number
  range_days: number
  utilization_rate: number
}

export interface EquipmentUtilizationReport {
  range: { start: string; end: string; range_days: number }
  items: EquipmentUtilizationItem[]
}

export function fetchEquipmentUtilizationReport(params: {
  start: string
  end: string
  limit?: number
  include_zero?: 0 | 1
}): Promise<EquipmentUtilizationReport> {
  return http.get<EquipmentUtilizationReport>('/reports/equipment-utilization/', { params }).then((r) => r.data)
}

export interface ConsumableMonthlyItem {
  month: string
  qty: number
}

export interface ConsumableMonthlyReport {
  year: number
  items: ConsumableMonthlyItem[]
}

export function fetchConsumableMonthlyReport(params: {
  year?: number
  consumable_id?: number
} = {}): Promise<ConsumableMonthlyReport> {
  return http.get<ConsumableMonthlyReport>('/reports/consumable-monthly/', { params }).then((r) => r.data)
}

