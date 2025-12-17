import type { FormItemRule } from 'element-plus'

export function requiredRule(message: string, trigger: 'blur' | 'change' = 'blur'): FormItemRule {
  return { required: true, message, trigger }
}

export function minLengthRule(min: number, message?: string, trigger: 'blur' | 'change' = 'blur'): FormItemRule {
  return { min, message: message ?? `至少 ${min} 位`, trigger }
}

export function emailRule(message = '邮箱格式不正确', trigger: 'blur' | 'change' = 'blur'): FormItemRule {
  return { type: 'email', message, trigger }
}

