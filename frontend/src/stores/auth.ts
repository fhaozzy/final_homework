import { defineStore } from 'pinia'

export interface AuthUser {
  id: number
  username: string
  real_name: string
  email: string
  phone: string
}

const ACCESS_TOKEN_KEY = 'lab_access_token'
const REFRESH_TOKEN_KEY = 'lab_refresh_token'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: localStorage.getItem(ACCESS_TOKEN_KEY) || '',
    refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY) || '',
    user: null as AuthUser | null,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken),
  },
  actions: {
    setTokens(tokens: { access: string; refresh: string }) {
      this.accessToken = tokens.access
      this.refreshToken = tokens.refresh
      localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access)
      localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh)
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
