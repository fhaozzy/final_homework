import type { Pinia } from 'pinia'
import { ElMessage } from 'element-plus'
import { RouterView, createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import { useAuthStore } from '../stores/auth'
import type { RoleCode } from '../types/rbac'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    meta: { requiresAuth: true, title: '首页' },
    children: [
      { path: '', redirect: '/dashboard' },
      {
        path: '/dashboard',
        name: 'dashboard',
        component: () => import('../views/DashboardView.vue'),
        meta: { title: '仪表盘' },
      },
      {
        path: '/equipment',
        component: RouterView,
        meta: { title: '设备台账' },
        children: [
          {
            path: '',
            name: 'equipment',
            component: () => import('../views/EquipmentListView.vue'),
          },
          {
            path: 'categories',
            name: 'equipment-categories',
            component: () => import('../views/EquipmentCategoriesView.vue'),
            meta: { title: '设备分类', roles: ['ADMIN'] as RoleCode[] },
          },
          {
            path: ':id',
            name: 'equipment-detail',
            component: () => import('../views/EquipmentDetailView.vue'),
            meta: { title: '设备详情' },
          },
        ],
      },
      {
        path: '/consumables',
        name: 'consumables',
        component: () => import('../views/ConsumablesView.vue'),
        meta: { title: '耗材库存' },
      },
      {
        path: '/borrow',
        component: RouterView,
        meta: { title: '借用流程' },
        children: [
          {
            path: 'requests',
            name: 'borrow-requests',
            component: () => import('../views/BorrowRequestsView.vue'),
            meta: { title: '借用单列表' },
          },
          {
            path: 'new',
            name: 'borrow-new',
            component: () => import('../views/BorrowRequestCreateView.vue'),
            meta: { title: '新建借用单' },
          },
          {
            path: ':id',
            name: 'borrow-detail',
            component: () => import('../views/BorrowRequestDetailView.vue'),
            meta: { title: '借用单详情' },
          },
        ],
      },
      {
        path: '/maintenance',
        name: 'maintenance',
        component: () => import('../views/MaintenanceView.vue'),
        meta: { title: '维修管理' },
      },
      {
        path: 'reports',
        component: RouterView,
        meta: { title: '统计报表', roles: ['TEACHER', 'ADMIN'] as RoleCode[] },
        children: [
          {
            path: 'borrow-top',
            name: 'report-borrow-top',
            component: () => import('../views/reports/BorrowTopReportView.vue'),
            meta: { title: '借用排行' },
          },
          {
            path: 'utilization',
            name: 'report-utilization',
            component: () => import('../views/reports/EquipmentUtilizationReportView.vue'),
            meta: { title: '设备利用率' },
          },
          {
            path: 'consumption',
            name: 'report-consumption',
            component: () => import('../views/reports/ConsumableMonthlyReportView.vue'),
            meta: { title: '耗材月消耗' },
          },
        ],
      },
      {
        path: 'admin',
        component: RouterView,
        meta: { title: '系统管理', roles: ['ADMIN'] as RoleCode[] },
        children: [
          {
            path: 'users',
            name: 'admin-users',
            component: () => import('../views/admin/AdminUsersView.vue'),
            meta: { title: '用户管理' },
          },
          {
            path: 'roles',
            name: 'admin-roles',
            component: () => import('../views/admin/AdminRolesView.vue'),
            meta: { title: '角色管理' },
          },
        ],
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

export function createAppRouter(pinia: Pinia) {
  const router = createRouter({
    history: createWebHistory(),
    routes,
  })

  router.beforeEach(async (to) => {
    const auth = useAuthStore(pinia)

    const requiresAuth = to.matched.some((r) => r.meta.requiresAuth)
    if (requiresAuth && !auth.isAuthenticated) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }

    if (to.name === 'login' && auth.isAuthenticated) {
      return { name: 'dashboard' }
    }

    if (requiresAuth) {
      await auth.ensurePermissionsLoaded()
    }

    const requiredRoles = to.meta.roles as RoleCode[] | undefined
    if (requiredRoles?.length && !auth.hasAnyRole(requiredRoles)) {
      ElMessage.warning('无权限访问该页面')
      return { name: 'dashboard' }
    }
  })

  return router
}
