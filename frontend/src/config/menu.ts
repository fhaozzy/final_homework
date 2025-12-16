import type { RoleCode } from '../types/rbac'

export interface MenuItem {
  key: string
  title: string
  path?: string
  rolesAny?: RoleCode[]
  children?: MenuItem[]
}

export const MENU_ITEMS: MenuItem[] = [
  { key: 'dashboard', title: '仪表盘', path: '/dashboard' },
  { key: 'equipment', title: '设备台账', path: '/equipment' },
  { key: 'consumables', title: '耗材库存', path: '/consumables' },
  { key: 'borrowing', title: '借用流程', path: '/borrow/requests' },
  { key: 'maintenance', title: '维修管理', path: '/maintenance', rolesAny: ['MAINTAINER', 'ADMIN'] },
  {
    key: 'reports',
    title: '统计报表',
    rolesAny: ['TEACHER', 'ADMIN'],
    children: [
      { key: 'report-borrow-top', title: '借用排行', path: '/reports/borrow-top' },
      { key: 'report-utilization', title: '设备利用率', path: '/reports/utilization' },
      { key: 'report-consumption', title: '耗材月消耗', path: '/reports/consumption' },
    ],
  },
  {
    key: 'admin',
    title: '系统管理',
    rolesAny: ['ADMIN'],
    children: [
      { key: 'admin-users', title: '用户管理', path: '/admin/users' },
      { key: 'admin-roles', title: '角色管理', path: '/admin/roles' },
    ],
  },
]
