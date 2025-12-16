import { defineStore } from 'pinia'

import { tokenObtainPair, tokenRefresh } from '../api/auth'
import { fetchMe } from '../api/me'
import { probeCanAdmin, probeCanMaintainWrite, probeCanViewReports } from '../api/rbac'
import type { RoleCode } from '../types/rbac'
import { normalizeRoleCode } from '../types/rbac'

export interface AuthUser {
  id: number
  username: string
  real_name: string
  email: string
  phone: string
  roles: RoleCode[]
}

const ACCESS_TOKEN_KEY = 'lab_access_token'
const REFRESH_TOKEN_KEY = 'lab_refresh_token'

type RbacMode = 'unknown' | 'roles' | 'fallback'

interface Capabilities {
  canViewReports: boolean
  canAdmin: boolean
  canMaintainWrite: boolean
}

let permissionsPromise: Promise<void> | null = null

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: localStorage.getItem(ACCESS_TOKEN_KEY) || '',
    refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY) || '',
    user: null as AuthUser | null,
    rbacMode: 'unknown' as RbacMode,
    permissionsLoaded: false,
    capabilities: {
      canViewReports: false,
      canAdmin: false,
      canMaintainWrite: false,
    } as Capabilities,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken),
    roles: (state) => state.user?.roles ?? [],
    inferredRole: (state): RoleCode | 'UNKNOWN' => {
      if (state.user?.roles?.length) {
        if (state.user.roles.includes('ADMIN')) return 'ADMIN'
        if (state.user.roles.includes('TEACHER')) return 'TEACHER'
        if (state.user.roles.includes('MAINTAINER')) return 'MAINTAINER'
        if (state.user.roles.includes('STUDENT')) return 'STUDENT'
      }

      if (state.rbacMode === 'fallback') {
        if (state.capabilities.canAdmin) return 'ADMIN'
        if (state.capabilities.canMaintainWrite) return 'MAINTAINER'
        if (state.capabilities.canViewReports) return 'TEACHER'
        return 'STUDENT'
      }

      return 'UNKNOWN'
    },
    isAdmin: (state) => {
      if (state.user?.roles?.includes('ADMIN')) return true
      if (state.rbacMode === 'fallback') return state.capabilities.canAdmin
      return false
    },
    canViewReports: (state) => {
      if (state.user?.roles?.includes('ADMIN') || state.user?.roles?.includes('TEACHER')) return true
      if (state.rbacMode === 'fallback') return state.capabilities.canViewReports
      return false
    },
  },
  actions: {
    async login(payload: { username: string; password: string }) {
      const tokens = await tokenObtainPair(payload)
      this.setTokens(tokens)
      await this.ensurePermissionsLoaded()
    },
    async refresh() {
      if (!this.refreshToken) {
        throw new Error('Missing refresh token')
      }
      const { access } = await tokenRefresh({ refresh: this.refreshToken })
      this.setAccessToken(access)
    },
    logout() {
      this.clearTokens()
      this.setUser(null)
      this.resetPermissions()
    },
    resetPermissions() {
      this.rbacMode = 'unknown'
      this.permissionsLoaded = false
      this.capabilities = { canViewReports: false, canAdmin: false, canMaintainWrite: false }
    },
    hasRole(role: RoleCode): boolean {
      if (this.user?.roles?.includes(role)) return true
      if (this.rbacMode === 'fallback') {
        if (role === 'ADMIN') return this.capabilities.canAdmin
        if (role === 'TEACHER') return this.capabilities.canViewReports || this.capabilities.canAdmin
        if (role === 'MAINTAINER') return this.capabilities.canMaintainWrite || this.capabilities.canAdmin
        if (role === 'STUDENT')
          return (
            !this.capabilities.canViewReports &&
            !this.capabilities.canAdmin &&
            !this.capabilities.canMaintainWrite
          )
      }
      return false
    },
    hasAnyRole(roles: RoleCode[]): boolean {
      return roles.some((role) => this.hasRole(role))
    },
    async ensurePermissionsLoaded() {
      if (!this.isAuthenticated) return
      if (this.permissionsLoaded) return
      if (permissionsPromise) return permissionsPromise

      permissionsPromise = this.bootstrapPermissions().finally(() => {
        permissionsPromise = null
      })
      return permissionsPromise
    },
    async bootstrapPermissions() {
      this.resetPermissions()

      try {
        const me = await fetchMe()
        const roles = (me.roles || [])
          .map((r) => normalizeRoleCode(r))
          .filter((r): r is RoleCode => Boolean(r))

        this.user = {
          id: me.id,
          username: me.username,
          real_name: me.real_name,
          email: me.email,
          phone: me.phone,
          roles,
        }

        this.rbacMode = 'roles'
        this.permissionsLoaded = true
        return
      } catch {
        // ignore and fall back to probing
      }

      const [canViewReports, canAdmin, canMaintainWrite] = await Promise.all([
        probeCanViewReports(),
        probeCanAdmin(),
        probeCanMaintainWrite(),
      ])
      this.capabilities = { canViewReports, canAdmin, canMaintainWrite }
      this.rbacMode = 'fallback'
      this.permissionsLoaded = true
    },
    setTokens(tokens: { access: string; refresh: string }) {
      this.accessToken = tokens.access
      this.refreshToken = tokens.refresh
      localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access)
      localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh)
    },
    setAccessToken(access: string) {
      this.accessToken = access
      localStorage.setItem(ACCESS_TOKEN_KEY, access)
    },
    clearTokens() {
      this.accessToken = ''
      this.refreshToken = ''
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
    },
    setUser(user: AuthUser | null) {
      this.user = user
    },
  },
})
