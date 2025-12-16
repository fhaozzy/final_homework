import { http } from './http'

export interface TokenPair {
  access: string
  refresh: string
}

export function tokenObtainPair(payload: {
  username: string
  password: string
}): Promise<TokenPair> {
  return http.post<TokenPair>('/auth/token/', payload).then((r) => r.data)
}

export function tokenRefresh(payload: { refresh: string }): Promise<{
  access: string
}> {
  return http
    .post<{ access: string }>('/auth/token/refresh/', payload)
    .then((r) => r.data)
}

