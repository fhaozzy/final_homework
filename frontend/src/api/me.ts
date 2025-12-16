import { http } from './http'

export interface Me {
  id: number
  username: string
  real_name: string
  email: string
  phone: string
  roles: string[]
  is_admin: boolean
}

export function fetchMe(): Promise<Me> {
  return http.get<Me>('/me/').then((r) => r.data)
}

