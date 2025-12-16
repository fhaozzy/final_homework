import { http } from './http'
import type { Paginated } from './types'

export interface EquipmentCategory {
  id: number
  code: string
  name: string
  description: string
  created_at: string
  updated_at: string
}

export interface Equipment {
  id: number
  code: string
  name: string
  category: EquipmentCategory
  status: string
  location: string
  purchase_date: string | null
  price: string | null
  vendor: string
  spec: string
  usable: boolean
  created_at: string
  updated_at: string
}

export interface EquipmentStatusLog {
  id: number
  equipment_id: number
  from_status: string
  to_status: string
  changed_by: number
  changed_by_username: string
  reason: string
  remark: string
  created_at: string
  updated_at: string
}

export function listEquipmentCategories(params: { page?: number } = {}): Promise<Paginated<EquipmentCategory>> {
  return http
    .get<Paginated<EquipmentCategory>>('/equipment-categories/', { params })
    .then((r) => r.data)
}

export async function fetchAllEquipmentCategories(): Promise<EquipmentCategory[]> {
  const first = await listEquipmentCategories({ page: 1 })
  const items: EquipmentCategory[] = [...first.results]

  const total = first.count
  const pageSize = first.results.length || 10
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  for (let page = 2; page <= totalPages; page += 1) {
    const resp = await listEquipmentCategories({ page })
    items.push(...resp.results)
    if (resp.results.length === 0) break
  }

  return items
}

export function createEquipmentCategory(payload: {
  code: string
  name: string
  description?: string
}): Promise<EquipmentCategory> {
  return http.post<EquipmentCategory>('/equipment-categories/', payload).then((r) => r.data)
}

export function updateEquipmentCategory(
  id: number,
  payload: { code: string; name: string; description?: string },
): Promise<EquipmentCategory> {
  return http.put<EquipmentCategory>(`/equipment-categories/${id}/`, payload).then((r) => r.data)
}

export function deleteEquipmentCategory(id: number): Promise<void> {
  return http.delete(`/equipment-categories/${id}/`).then(() => undefined)
}

export function listEquipment(params: {
  page?: number
  status?: string
  category?: string | number
  keyword?: string
}): Promise<Paginated<Equipment>> {
  return http.get<Paginated<Equipment>>('/equipment/', { params }).then((r) => r.data)
}

export function fetchEquipment(id: number): Promise<Equipment> {
  return http.get<Equipment>(`/equipment/${id}/`).then((r) => r.data)
}

export function createEquipment(payload: {
  code: string
  name: string
  category_id: number
  status?: string
  location?: string
  purchase_date?: string | null
  price?: number | string | null
  vendor?: string
  spec?: string
  usable?: boolean
}): Promise<Equipment> {
  return http.post<Equipment>('/equipment/', payload).then((r) => r.data)
}

export function updateEquipment(
  id: number,
  payload: {
    code: string
    name: string
    category_id: number
    status?: string
    location?: string
    purchase_date?: string | null
    price?: number | string | null
    vendor?: string
    spec?: string
    usable?: boolean
  },
): Promise<Equipment> {
  return http.put<Equipment>(`/equipment/${id}/`, payload).then((r) => r.data)
}

export function deleteEquipment(id: number): Promise<void> {
  return http.delete(`/equipment/${id}/`).then(() => undefined)
}

export function fetchEquipmentLogs(id: number): Promise<EquipmentStatusLog[]> {
  return http.get<EquipmentStatusLog[]>(`/equipment/${id}/logs/`).then((r) => r.data)
}

export function changeEquipmentStatus(
  id: number,
  payload: { to_status: string; reason?: string; remark?: string },
): Promise<Equipment> {
  return http.post<Equipment>(`/equipment/${id}/status/`, payload).then((r) => r.data)
}

