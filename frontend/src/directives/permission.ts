import type { Directive } from 'vue'

import { useAuthStore } from '../stores/auth'
import type { RoleCode } from '../types/rbac'

type PermissionBinding =
  | RoleCode
  | RoleCode[]
  | {
      anyOf?: RoleCode[]
    }

function resolveRoles(bindingValue: PermissionBinding): RoleCode[] {
  if (typeof bindingValue === 'string') return [bindingValue]
  if (Array.isArray(bindingValue)) return bindingValue
  return bindingValue.anyOf ?? []
}

function setVisible(el: HTMLElement, visible: boolean) {
  const key = 'data-original-display'
  if (visible) {
    const original = el.getAttribute(key)
    el.style.display = original ?? ''
    return
  }

  if (!el.hasAttribute(key)) {
    el.setAttribute(key, el.style.display || '')
  }
  el.style.display = 'none'
}

export const permissionDirective: Directive<HTMLElement, PermissionBinding> = {
  mounted(el, binding) {
    const auth = useAuthStore()
    const roles = resolveRoles(binding.value)
    setVisible(el, roles.length === 0 || auth.hasAnyRole(roles))
  },
  updated(el, binding) {
    const auth = useAuthStore()
    const roles = resolveRoles(binding.value)
    setVisible(el, roles.length === 0 || auth.hasAnyRole(roles))
  },
}

