import { useAuthStore } from '../stores/auth'
import type { RoleCode } from '../types/rbac'

export function hasRole(role: RoleCode): boolean {
  return useAuthStore().hasRole(role)
}

export function hasAnyRole(roles: RoleCode[]): boolean {
  return useAuthStore().hasAnyRole(roles)
}

