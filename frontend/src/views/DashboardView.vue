<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const refreshing = ref(false)
const accessPreview = computed(() => {
  if (!auth.accessToken) return ''
  return `${auth.accessToken.slice(0, 24)}...`
})

async function onRefresh() {
  refreshing.value = true
  try {
    await auth.refresh()
    ElMessage.success('已刷新 access token')
  } catch {
    ElMessage.error('刷新失败，请重新登录')
    auth.logout()
    await router.replace({ name: 'login' })
  } finally {
    refreshing.value = false
  }
}

async function onLogout() {
  auth.logout()
  await router.replace({ name: 'login' })
}
</script>

<template>
  <div class="page">
    <el-card class="card">
      <template #header>
        <div class="title">仪表盘</div>
      </template>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="是否登录">
          {{ auth.isAuthenticated ? '是' : '否' }}
        </el-descriptions-item>
        <el-descriptions-item label="Access Token">
          {{ accessPreview }}
        </el-descriptions-item>
      </el-descriptions>

      <el-space class="actions">
        <el-button type="primary" :loading="refreshing" @click="onRefresh">
          刷新 Token
        </el-button>
        <el-button @click="onLogout">退出登录</el-button>
      </el-space>
    </el-card>
  </div>
</template>

<style scoped>
.page {
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.card {
  width: 640px;
}

.title {
  font-size: 16px;
  font-weight: 600;
}

.actions {
  margin-top: 16px;
}
</style>
