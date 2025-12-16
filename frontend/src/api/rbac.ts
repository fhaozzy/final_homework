import axios from 'axios'

import { http } from './http'

function isHttpStatus(error: unknown, status: number): boolean {
  return axios.isAxiosError(error) && error.response?.status === status
}

export async function probeCanViewReports(): Promise<boolean> {
  try {
    await http.get('/reports/borrow-top/', { params: { limit: 1 } })
    return true
  } catch (error) {
    if (isHttpStatus(error, 403) || isHttpStatus(error, 401)) return false
    return false
  }
}

export async function probeCanAdmin(): Promise<boolean> {
  try {
    await http.get('/users/', { params: { page: 1 } })
    return true
  } catch (error) {
    if (isHttpStatus(error, 403) || isHttpStatus(error, 401) || isHttpStatus(error, 404)) return false
    return false
  }
}

export async function probeCanMaintainWrite(): Promise<boolean> {
  try {
    await http.post('/maintenance/', {})
    return true
  } catch (error) {
    if (isHttpStatus(error, 403) || isHttpStatus(error, 401)) return false
    // Permission allowed but payload invalid
    if (isHttpStatus(error, 400)) return true
    return false
  }
}
