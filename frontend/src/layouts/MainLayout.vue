<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { MENU_ITEMS, type MenuItem } from '../config/menu'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const collapsed = ref(false)

const activeMenuPath = computed(() => {
  if (route.path.startsWith('/equipment')) return '/equipment'
  return route.path
})

const breadcrumbs = computed(() => {
  return route.matched
    .filter((r) => typeof r.meta?.title === 'string')
    .map((r) => ({ title: r.meta.title as string, path: r.path }))
})

function canShowItem(item: MenuItem): boolean {
  if (item.rolesAny?.length) {
    if (!auth.permissionsLoaded) return false
    return auth.hasAnyRole(item.rolesAny)
  }
  return true
}

const visibleMenu = computed(() => {
  const filterItems = (items: MenuItem[]): MenuItem[] => {
    return items
      .filter((item) => canShowItem(item))
      .map((item) => {
        if (!item.children?.length) return item
        const children = filterItems(item.children)
        return children.length ? { ...item, children } : item
      })
  }
  return filterItems(MENU_ITEMS)
})

const permissionHint = computed(() => {
  if (!auth.permissionsLoaded) return '加载中'
  if (auth.rbacMode === 'fallback') return '降级：后端未提供角色接口，按 403 探测'
  if (auth.rbacMode === 'roles') return '角色：来自后端'
  return '未知'
})

async function onRefreshToken() {
  try {
    await auth.refresh()
    ElMessage.success('已刷新 Token')
  } catch {
    ElMessage.error('刷新失败，请重新登录')
    auth.logout()
    await router.replace({ name: 'login' })
  }
}

async function onLogout() {
  auth.logout()
  await router.replace({ name: 'login' })
}

onMounted(() => {
  if (auth.isAuthenticated) {
    void auth.ensurePermissionsLoaded()
  }
})
</script>

<template>
  <el-container class="layout">
    <el-aside class="aside" :width="collapsed ? '64px' : '220px'">
      <div class="brand" :class="{ collapsed }">
        <span v-if="!collapsed">Lab Manage</span>
        <span v-else>LM</span>
      </div>

      <el-menu :default-active="activeMenuPath" router class="menu" :collapse="collapsed">
        <template v-for="item in visibleMenu" :key="item.key">
          <el-sub-menu v-if="item.children?.length" :index="item.key">
            <template #title>
              <span>{{ item.title }}</span>
            </template>
            <el-menu-item
              v-for="child in item.children"
              :key="child.key"
              :index="child.path || child.key"
            >
              {{ child.title }}
            </el-menu-item>
          </el-sub-menu>

          <el-menu-item v-else :index="item.path || item.key">
            {{ item.title }}
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-button text @click="collapsed = !collapsed">
            {{ collapsed ? '展开' : '收起' }}
          </el-button>

          <el-breadcrumb separator="/">
            <el-breadcrumb-item v-for="bc in breadcrumbs" :key="bc.path">
              {{ bc.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <el-tag v-if="auth.rbacMode === 'fallback'" type="warning">权限降级</el-tag>
          <el-tooltip :content="permissionHint" placement="bottom">
            <el-tag type="info">{{ auth.inferredRole }}</el-tag>
          </el-tooltip>

          <el-button text @click="onRefreshToken">刷新 Token</el-button>
          <el-button text @click="onLogout">退出</el-button>
        </div>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout {
  height: 100%;
}

.aside {
  border-right: 1px solid var(--el-border-color);
  background: #ffffff;
}

.brand {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  font-weight: 700;
  border-bottom: 1px solid var(--el-border-color);
}

.brand.collapsed {
  justify-content: center;
  padding: 0;
}

.menu {
  border-right: none;
}

.header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--el-border-color);
  background: #ffffff;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.main {
  padding: 16px;
}
</style>
