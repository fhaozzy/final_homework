import axios, { AxiosError } from 'axios'
import type { Pinia } from 'pinia'

import { useAuthStore } from '../stores/auth'
import { API_BASE_URL, HTTP_TIMEOUT_MS, http } from './http'

let interceptorsInstalled = false
let refreshPromise: Promise<string> | null = null

const authHttp = axios.create({
  baseURL: API_BASE_URL,
  timeout: HTTP_TIMEOUT_MS,
})

function setAuthorizationHeader(headers: unknown, accessToken: string) {
  if (!headers) return { Authorization: `Bearer ${accessToken}` }

  if (typeof (headers as { set?: unknown }).set === 'function') {
    ;(headers as { set: (k: string, v: string) => void }).set(
      'Authorization',
      `Bearer ${accessToken}`,
    )
    return headers
  }

  ;(headers as Record<string, string>).Authorization = `Bearer ${accessToken}`
  return headers
}

async function refreshAccessToken(refreshToken: string): Promise<string> {
  const { data } = await authHttp.post<{ access: string }>('/auth/token/refresh/', {
    refresh: refreshToken,
  })
  return data.access
}

export function setupHttpInterceptors(pinia: Pinia) {
  if (interceptorsInstalled) return
  interceptorsInstalled = true

  const auth = useAuthStore(pinia)

  http.interceptors.request.use((config) => {
    if (!auth.accessToken) return config
    config.headers = setAuthorizationHeader(config.headers, auth.accessToken) as any
    return config
  })

  http.interceptors.response.use(
    (resp) => resp,
    async (error: AxiosError) => {
      const status = error.response?.status
      const originalRequest = error.config as any
      const url = typeof originalRequest?.url === 'string' ? originalRequest.url : ''

      if (!originalRequest || status !== 401) {
        return Promise.reject(error)
      }

      if (url.includes('/auth/token/')) {
        return Promise.reject(error)
      }

      if (originalRequest._retry) {
        auth.logout()
        return Promise.reject(error)
      }

      if (!auth.refreshToken) {
        auth.logout()
        return Promise.reject(error)
      }

      originalRequest._retry = true

      try {
        if (!refreshPromise) {
          refreshPromise = refreshAccessToken(auth.refreshToken)
            .then((access) => {
              auth.setAccessToken(access)
              return access
            })
            .finally(() => {
              refreshPromise = null
            })
        }

        const access = await refreshPromise
        originalRequest.headers = setAuthorizationHeader(originalRequest.headers, access)
        return http(originalRequest)
      } catch {
        auth.logout()
        return Promise.reject(error)
      }
    },
  )
}

