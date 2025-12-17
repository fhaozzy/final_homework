<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { fetchEquipmentUtilizationReport, type EquipmentUtilizationReport } from '../../api/reports'

const loading = ref(false)
const errorMessage = ref('')
const report = ref<EquipmentUtilizationReport | null>(null)

function toDateString(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function daysAgo(n: number): Date {
  const date = new Date()
  date.setDate(date.getDate() - n)
  return date
}

const form = reactive({
  range: [toDateString(daysAgo(29)), toDateString(new Date())] as string[],
  includeZero: true,
  limit: 200,
})

const hasRange = computed(() => form.range?.length === 2 && Boolean(form.range[0]) && Boolean(form.range[1]))

function normalizePercentage(value: number): number {
  if (!Number.isFinite(value)) return 0
  if (value < 0) return 0
  if (value > 100) return 100
  return value
}

function utilizationPercent(rate: number): number {
  return normalizePercentage(Math.round(rate * 100))
}

async function load() {
  const [start, end] = form.range
  if (!hasRange.value || !start || !end) {
    errorMessage.value = '请选择日期区间'
    report.value = null
    return
  }

  loading.value = true
  errorMessage.value = ''
  try {
    report.value = await fetchEquipmentUtilizationReport({
      start,
      end,
      limit: form.limit || 200,
      include_zero: form.includeZero ? 1 : 0,
    })
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
    report.value = null
  } finally {
    loading.value = false
  }
}

function onSearch() {
  void load()
}

function onReset() {
  form.range = [toDateString(daysAgo(29)), toDateString(new Date())]
  form.includeZero = true
  form.limit = 200
  void load()
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
          <div class="title">设备利用率</div>
          <div class="actions">
            <el-button @click="load">刷新</el-button>
          </div>
        </div>
      </template>

      <el-form :inline="true" class="filters" @submit.prevent>
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
          />
        </el-form-item>
        <el-form-item label="包含零利用率">
          <el-switch v-model="form.includeZero" />
        </el-form-item>
        <el-form-item label="Limit">
          <el-input-number v-model="form.limit" :min="1" :max="5000" style="width: 160px" />
        </el-form-item>
        <el-form-item>
          <el-space>
            <el-button type="primary" @click="onSearch">查询</el-button>
            <el-button @click="onReset">重置</el-button>
          </el-space>
        </el-form-item>
      </el-form>

      <el-alert v-if="errorMessage" :title="errorMessage" type="warning" show-icon />

      <template v-else-if="report">
        <el-alert
          :title="`区间：${report.range.start} ~ ${report.range.end}（共 ${report.range.range_days} 天）`"
          type="info"
          show-icon
          class="mb-12"
        />

        <el-table v-if="report.items.length" :data="report.items" stripe style="width: 100%">
          <el-table-column prop="equipment_code" label="设备编码" width="160" />
          <el-table-column prop="equipment_name" label="设备名称" min-width="220" />
          <el-table-column prop="borrowed_days" label="借用天数" width="110" align="right" />
          <el-table-column prop="range_days" label="区间天数" width="110" align="right" />
          <el-table-column label="利用率" width="260">
            <template #default="{ row }">
              <el-progress :percentage="utilizationPercent(row.utilization_rate)" :stroke-width="16" />
            </template>
          </el-table-column>
          <el-table-column label="数值" width="120" align="right">
            <template #default="{ row }">
              {{ utilizationPercent(row.utilization_rate) }}%
            </template>
          </el-table-column>
        </el-table>

        <el-empty v-else description="暂无数据" />
      </template>
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

.mb-12 {
  margin-bottom: 12px;
}
</style>
