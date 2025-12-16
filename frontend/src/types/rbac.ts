export type RoleCode = 'STUDENT' | 'TEACHER' | 'MAINTAINER' | 'ADMIN'

export function normalizeRoleCode(value: string): RoleCode | null {
  const code = value.trim().toUpperCase()
  if (code === 'STUDENT') return 'STUDENT'
  if (code === 'TEACHER') return 'TEACHER'
  if (code === 'MAINTAINER') return 'MAINTAINER'
  if (code === 'ADMIN') return 'ADMIN'
  return null
}

