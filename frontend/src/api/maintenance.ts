import { http } from './http'
import type { Paginated } from './types'

export type MaintenanceStatus = 'OPEN' | 'IN_PROGRESS' | 'DONE'

export interface Maintenance {
  id: number
  equipment_id: number
  equipment_code: string
  equipment_name: string
  title: string
  description: string
  status: MaintenanceStatus
  assigned_to: number | null
  assigned_to_username: string
  cost: string | null
  started_at: string | null
  finished_at: string | null
  created_at: string
  updated_at: string
}

export function listMaintenance(params: {
  page?: number
  status?: MaintenanceStatus
  equipment?: number
  keyword?: string
} = {}): Promise<Paginated<Maintenance>> {
  return http.get<Paginated<Maintenance>>('/maintenance/', { params }).then((r) => r.data)
}

export function createMaintenance(payload: {
  equipment: number
  title: string
  description?: string
  assigned_to?: number | null
  cost?: number | string | null
}): Promise<Maintenance> {
  return http.post<Maintenance>('/maintenance/', payload).then((r) => r.data)
}

export function patchMaintenance(
  id: number,
  payload: Partial<{
    title: string
    description: string
    status: MaintenanceStatus
    assigned_to: number | null
    cost: number | string | null
  }>,
): Promise<Maintenance> {
  return http.patch<Maintenance>(`/maintenance/${id}/`, payload).then((r) => r.data)
}

