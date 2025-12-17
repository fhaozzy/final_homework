<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { fetchBorrowTopReport, type BorrowTopReport } from '../../api/reports'

const loading = ref(false)
const errorMessage = ref('')
const report = ref<BorrowTopReport | null>(null)

const form = reactive({
  limit: 10,
  range: [] as string[],
})

const maxBorrowCount = computed(() => {
  const items = report.value?.items ?? []
  return items.reduce((max, it) => Math.max(max, it.borrow_count), 0)
})

function normalizePercentage(value: number): number {
  if (!Number.isFinite(value)) return 0
  if (value < 0) return 0
  if (value > 100) return 100
  return value
}

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    const params: Record<string, any> = { limit: form.limit || 10 }
    if (form.range?.length === 2) {
      params.start = form.range[0]
      params.end = form.range[1]
    }
    report.value = await fetchBorrowTopReport(params)
  } catch (err: any) {
    const status = err?.response?.status
    if (status === 403) {
      errorMessage.value = '无权限访问该报表（仅老师/管理员可读）'
    } else if (status === 401) {
      errorMessage.value = '未登录或登录已过期'
    } else {
      const data = err?.response?.data
      errorMessage.value = data?.detail || data?.range || '加载失败'
    }
  } finally {
    loading.value = false
  }
}

function onSearch() {
  void load()
}

function onReset() {
  form.limit = 10
  form.range = []
  void load()
}

function onRangeChange(value: string[] | null) {
  if (!value) {
    form.range = []
  }
}

function formatBarPercentage(count: number): number {
  if (maxBorrowCount.value <= 0) return 0
  return normalizePercentage(Math.round((count / maxBorrowCount.value) * 100))
}

function formatBarLabel(count: number): string {
  return String(count)
}

onMounted(() => {
  void load()
})
</script>

<template>
  <el-space direction="vertical" fill size="large">
    <el-card v-loading="loading">
      <template #header>
        <div class="header">
          <div class="title">借用排行</div>
          <div class="actions">
            <el-button @click="load">刷新</el-button>
          </div>
        </div>
      </template>

      <el-form :inline="true" class="filters" @submit.prevent>
        <el-form-item label="Top">
          <el-input-number v-model="form.limit" :min="1" :max="200" style="width: 140px" />
        </el-form-item>
        <el-form-item label="日期区间">
          <el-date-picker
            v-model="form.range"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="~"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            clearable
            style="width: 320px"
            @change="onRangeChange"
          />
        </el-form-item>
        <el-form-item>
          <el-space>
            <el-button type="primary" @click="onSearch">查询</el-button>
            <el-button @click="onReset">重置</el-button>
          </el-space>
        </el-form-item>
      </el-form>

      <el-alert v-if="errorMessage" :title="errorMessage" type="warning" show-icon />

      <el-table v-else-if="report?.items?.length" :data="report.items" stripe style="width: 100%">
        <el-table-column prop="equipment_code" label="设备编码" width="160" />
        <el-table-column prop="equipment_name" label="设备名称" min-width="220" />
        <el-table-column prop="borrow_count" label="借用次数" width="110" align="right" />
        <el-table-column label="图表" min-width="260">
          <template #default="{ row }">
            <el-progress
              :percentage="formatBarPercentage(row.borrow_count)"
              :format="() => formatBarLabel(row.borrow_count)"
              :stroke-width="16"
            />
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-else-if="!loading" description="暂无数据" />
    </el-card>
  </el-space>
</template>

<style scoped>
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.title {
  font-size: 16px;
  font-weight: 600;
}

.actions {
  display: flex;
  gap: 10px;
}

.filters {
  margin-bottom: 8px;
}
</style>
