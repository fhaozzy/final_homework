import { http } from './http'
import type { Paginated } from './types'

export interface User {
  id: number
  username: string
  email: string
  real_name: string
  phone: string
  is_active: boolean
  is_staff: boolean
  is_superuser: boolean
  last_login: string | null
  date_joined: string
  created_at: string
  updated_at: string
}

export function listUsers(params: { page?: number } = {}): Promise<Paginated<User>> {
  return http.get<Paginated<User>>('/users/', { params }).then((r) => r.data)
}

export async function fetchAllUsers(): Promise<User[]> {
  const first = await listUsers({ page: 1 })
  const items: User[] = [...first.results]

  const total = first.count
  const pageSize = first.results.length || 10
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  for (let page = 2; page <= totalPages; page += 1) {
    const resp = await listUsers({ page })
    items.push(...resp.results)
    if (resp.results.length === 0) break
  }

  return items
}

export function createUser(payload: {
  username: string
  password: string
  email?: string
  real_name?: string
  phone?: string
  is_active?: boolean
}): Promise<User> {
  return http.post<User>('/users/', payload).then((r) => r.data)
}

export function updateUser(
  id: number,
  payload: {
    username: string
    password?: string
    email?: string
    real_name?: string
    phone?: string
    is_active?: boolean
  },
): Promise<User> {
  return http.put<User>(`/users/${id}/`, payload).then((r) => r.data)
}

export function deleteUser(id: number): Promise<void> {
  return http.delete(`/users/${id}/`).then(() => undefined)
}

export function activateUser(id: number): Promise<User> {
  return http.patch<User>(`/users/${id}/activate/`).then((r) => r.data)
}

export function deactivateUser(id: number): Promise<User> {
  return http.patch<User>(`/users/${id}/deactivate/`).then((r) => r.data)
}

export interface Role {
  id: number
  code: string
  name: string
  created_at: string
  updated_at: string
}

export function listRoles(params: { page?: number } = {}): Promise<Paginated<Role>> {
  return http.get<Paginated<Role>>('/roles/', { params }).then((r) => r.data)
}

export async function fetchAllRoles(): Promise<Role[]> {
  const first = await listRoles({ page: 1 })
  const items: Role[] = [...first.results]

  const total = first.count
  const pageSize = first.results.length || 10
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  for (let page = 2; page <= totalPages; page += 1) {
    const resp = await listRoles({ page })
    items.push(...resp.results)
    if (resp.results.length === 0) break
  }

  return items
}

export function createRole(payload: { code: string; name: string }): Promise<Role> {
  return http.post<Role>('/roles/', payload).then((r) => r.data)
}

export function updateRole(id: number, payload: { code: string; name: string }): Promise<Role> {
  return http.put<Role>(`/roles/${id}/`, payload).then((r) => r.data)
}

export function deleteRole(id: number): Promise<void> {
  return http.delete(`/roles/${id}/`).then(() => undefined)
}

export interface UserRole {
  id: number
  user: number
  user_username: string
  role: number
  role_code: string
  role_name: string
  created_at: string
  updated_at: string
}

export function listUserRoles(params: { page?: number } = {}): Promise<Paginated<UserRole>> {
  return http.get<Paginated<UserRole>>('/user-roles/', { params }).then((r) => r.data)
}

export async function fetchAllUserRoles(): Promise<UserRole[]> {
  const first = await listUserRoles({ page: 1 })
  const items: UserRole[] = [...first.results]

  const total = first.count
  const pageSize = first.results.length || 10
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  for (let page = 2; page <= totalPages; page += 1) {
    const resp = await listUserRoles({ page })
    items.push(...resp.results)
    if (resp.results.length === 0) break
  }

  return items
}

export function createUserRole(payload: { user: number; role: number }): Promise<UserRole> {
  return http.post<UserRole>('/user-roles/', payload).then((r) => r.data)
}

export function deleteUserRole(id: number): Promise<void> {
  return http.delete(`/user-roles/${id}/`).then(() => undefined)
}

