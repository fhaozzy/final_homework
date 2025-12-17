<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { fetchAllConsumables, type Consumable } from '../../api/consumables'
import { fetchConsumableMonthlyReport, type ConsumableMonthlyReport } from '../../api/reports'

const loading = ref(false)
const errorMessage = ref('')
const report = ref<ConsumableMonthlyReport | null>(null)

const allConsumables = ref<Consumable[]>([])
const consumableLoading = ref(false)

function currentYear(): number {
  return new Date().getFullYear()
}

const form = reactive({
  year: currentYear(),
  consumableId: undefined as number | undefined,
})

const consumableOptions = computed(() =>
  allConsumables.value.map((c) => ({ label: `${c.name}(${c.code})`, value: c.id })),
)

const maxQty = computed(() => {
  const items = report.value?.items ?? []
  return items.reduce((max, it) => Math.max(max, it.qty), 0)
})

const totalQty = computed(() => {
  const items = report.value?.items ?? []
  return items.reduce((sum, it) => sum + it.qty, 0)
})

function normalizePercentage(value: number): number {
  if (!Number.isFinite(value)) return 0
  if (value < 0) return 0
  if (value > 100) return 100
  return value
}

function barPercentage(qty: number): number {
  if (maxQty.value <= 0) return 0
  return normalizePercentage(Math.round((qty / maxQty.value) * 100))
}

async function loadConsumables() {
  consumableLoading.value = true
  try {
    allConsumables.value = await fetchAllConsumables()
  } catch {
    allConsumables.value = []
  } finally {
    consumableLoading.value = false
  }
}

async function loadReport() {
  loading.value = true
  errorMessage.value = ''
  try {
    report.value = await fetchConsumableMonthlyReport({
      year: form.year || currentYear(),
      consumable_id: form.consumableId,
    })
  } catch (err: any) {
    const status = err?.response?.status
    if (status === 403) {
      errorMessage.value = '无权限访问该报表（仅老师/管理员可读）'
    } else if (status === 401) {
      errorMessage.value = '未登录或登录已过期'
    } else {
      const data = err?.response?.data
      errorMessage.value = data?.detail || data?.year || data?.consumable_id || '加载失败'
    }
    report.value = null
  } finally {
    loading.value = false
  }
}

function onSearch() {
  void loadReport()
}

function onReset() {
  form.year = currentYear()
  form.consumableId = undefined
  void loadReport()
}

onMounted(async () => {
  void loadConsumables()
  await loadReport()
})
</script>

<template>
  <el-space direction="vertical" fill size="large">
    <el-card v-loading="loading">
      <template #header>
        <div class="header">
          <div class="title">耗材月消耗</div>
          <div class="actions">
            <el-button @click="loadReport">刷新</el-button>
          </div>
        </div>
      </template>

      <el-form :inline="true" class="filters" @submit.prevent>
        <el-form-item label="年份">
          <el-input-number v-model="form.year" :min="2000" :max="2100" style="width: 160px" />
        </el-form-item>
        <el-form-item label="耗材(可选)">
          <el-select
            v-model="form.consumableId"
            clearable
            filterable
            :loading="consumableLoading"
            placeholder="全部耗材"
            style="width: 320px"
          >
            <el-option v-for="opt in consumableOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
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
          :title="`年份：${report.year}，总消耗：${totalQty}（单位：按出库数量统计）`"
          type="info"
          show-icon
          class="mb-12"
        />

        <el-table v-if="report.items.length" :data="report.items" stripe style="width: 100%">
          <el-table-column prop="month" label="月份" width="140" />
          <el-table-column prop="qty" label="消耗量" width="120" align="right" />
          <el-table-column label="图表" min-width="260">
            <template #default="{ row }">
              <el-progress :percentage="barPercentage(row.qty)" :format="() => String(row.qty)" :stroke-width="16" />
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
