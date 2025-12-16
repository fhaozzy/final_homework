import { http } from './http'
import type { Paginated } from './types'

export interface Consumable {
  id: number
  code: string
  name: string
  unit: string
  category: string
  safety_stock: number
  current_qty: number
  location: string
  created_at: string
  updated_at: string
}

export function listConsumables(params: { page?: number } = {}): Promise<Paginated<Consumable>> {
  return http.get<Paginated<Consumable>>('/consumables/', { params }).then((r) => r.data)
}

export async function fetchAllConsumables(): Promise<Consumable[]> {
  const first = await listConsumables({ page: 1 })
  const items: Consumable[] = [...first.results]

  const total = first.count
  const pageSize = first.results.length || 10
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  for (let page = 2; page <= totalPages; page += 1) {
    const resp = await listConsumables({ page })
    items.push(...resp.results)
    if (resp.results.length === 0) break
  }

  return items
}

export function createConsumable(payload: {
  code: string
  name: string
  unit: string
  category?: string
  safety_stock?: number
  location?: string
}): Promise<Consumable> {
  return http.post<Consumable>('/consumables/', payload).then((r) => r.data)
}

export function updateConsumable(
  id: number,
  payload: { code: string; name: string; unit: string; category?: string; safety_stock?: number; location?: string },
): Promise<Consumable> {
  return http.put<Consumable>(`/consumables/${id}/`, payload).then((r) => r.data)
}

export function deleteConsumable(id: number): Promise<void> {
  return http.delete(`/consumables/${id}/`).then(() => undefined)
}

export function listConsumableWarnings(): Promise<Consumable[]> {
  return http.get<Consumable[]>('/consumables/warnings/').then((r) => r.data)
}

