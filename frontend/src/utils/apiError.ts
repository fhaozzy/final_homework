import axios from 'axios'
import { ElMessage } from 'element-plus'

function stringifyValue(value: unknown): string {
  if (value == null) return ''
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  if (Array.isArray(value)) return value.map((v) => stringifyValue(v)).filter(Boolean).join('；')
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value)
    } catch {
      return String(value)
    }
  }
  return String(value)
}

function extractDetail(data: unknown): string {
  if (!data || typeof data !== 'object') return ''
  const obj = data as Record<string, unknown>
  const detail = obj.detail
  if (typeof detail === 'string' && detail.trim()) return detail.trim()
  return ''
}

function extractFieldErrors(data: unknown): string {
  if (!data || typeof data !== 'object') return ''
  const obj = data as Record<string, unknown>
  const parts: string[] = []

  for (const [key, value] of Object.entries(obj)) {
    if (key === 'detail') continue
    const text = stringifyValue(value).trim()
    if (!text) continue
    parts.push(`${key}: ${text}`)
  }

  return parts.join('；')
}

export function getApiErrorMessage(error: unknown, fallback = '请求失败'): string {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status
    const data = error.response?.data

    if (!status) {
      return error.message || fallback
    }

    if (status === 401) return '未登录或登录已过期'
    if (status === 403) return '无权限执行此操作'
    if (status === 404) return '资源不存在'
    if (status >= 500) return '服务器异常，请稍后重试'

    if (typeof data === 'string' && data.trim()) return data.trim()

    const detail = extractDetail(data)
    if (detail) return detail

    const fieldErrors = extractFieldErrors(data)
    if (fieldErrors) return fieldErrors

    return fallback
  }

  if (error instanceof Error) {
    return error.message || fallback
  }

  return fallback
}

export function notifyApiError(error: unknown, fallback = '请求失败') {
  ElMessage.error(getApiErrorMessage(error, fallback))
}

