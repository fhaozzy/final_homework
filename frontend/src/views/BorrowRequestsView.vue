<script setup lang="ts">
import { computed } from 'vue'

import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const hint = computed(() => {
  if (!auth.permissionsLoaded) return '权限加载中...'
  if (auth.rbacMode === 'fallback')
    return '权限降级：后端未提供 /me/ 角色接口，前端通过调用接口(403)探测并隐藏入口。'
  return '权限来源：后端角色。'
})
</script>

<template>
  <el-space direction="vertical" fill>
    <el-card>
      <template #header>
        <div>借用流程</div>
      </template>

      <el-alert :title="hint" type="warning" show-icon />

      <el-divider />

      <div class="section-title">按钮级权限演示</div>
      <el-space>
        <el-button type="primary">创建申请（所有登录用户）</el-button>
        <el-button v-permission="'ADMIN'" type="success">管理员审批</el-button>
        <el-button v-permission="'ADMIN'" type="warning">管理员出库</el-button>
        <el-button v-permission="'ADMIN'" type="danger">管理员归还验收</el-button>
      </el-space>
    </el-card>
  </el-space>
</template>

<style scoped>
.section-title {
  font-weight: 600;
  margin-bottom: 8px;
}
</style>

