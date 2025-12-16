<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { createBorrowRequest } from '../api/borrowing'
import {
  fetchAllEquipmentCategories,
  listEquipment,
  type Equipment,
  type EquipmentCategory,
} from '../api/equipment'
import { getEquipmentStatusLabel, getEquipmentStatusTagType } from '../constants/equipment'

const router = useRouter()

const saving = ref(false)
const formRef = ref<FormInstance>()
const form = reactive({
  purpose: '',
  expected_return_date: '' as string | '',
  remark: '',
})

const rules: FormRules = {
  purpose: [{ required: false }],
}

const categories = ref<EquipmentCategory[]>([])
const categoryOptions = computed(() => categories.value.map((c) => ({ label: `${c.name}(${c.code})`, value: c.id })))

const equipmentLoading = ref(false)
const equipmentList = ref<Equipment[]>([])
const equipmentTotal = ref(0)
const equipmentPage = ref(1)
const equipmentPageSize = ref(10)

const filters = reactive({
  categoryId: undefined as number | undefined,
  keyword: '',
})

const selected = ref<Equipment[]>([])
const selectedIds = computed(() => new Set(selected.value.map((e) => e.id)))

async function fetchCategories() {
  categories.value = await fetchAllEquipmentCategories()
}

async function fetchEquipmentList() {
  equipmentLoading.value = true
  try {
    const data = await listEquipment({
      page: equipmentPage.value,
      status: 'AVAILABLE',
      category: filters.categoryId || undefined,
      keyword: filters.keyword.trim() || undefined,
    })
    equipmentList.value = data.results
    equipmentTotal.value = data.count
    if (equipmentPage.value === 1 && data.results.length) {
      equipmentPageSize.value = data.results.length
    }
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '加载设备失败')
  } finally {
    equipmentLoading.value = false
  }
}

function onSearch() {
  equipmentPage.value = 1
  void fetchEquipmentList()
}

function onReset() {
  filters.categoryId = undefined
  filters.keyword = ''
  equipmentPage.value = 1
  void fetchEquipmentList()
}

function addEquipment(row: Equipment) {
  if (selectedIds.value.has(row.id)) {
    ElMessage.warning('该设备已加入列表')
    return
  }
  if (row.status !== 'AVAILABLE') {
    ElMessage.warning('仅可借用状态为 AVAILABLE 的设备')
    return
  }
  selected.value = [...selected.value, row]
}

function removeEquipment(id: number) {
  selected.value = selected.value.filter((e) => e.id !== id)
}

async function clearSelected() {
  try {
    await ElMessageBox.confirm('确认清空已选设备？', '提示', { type: 'warning' })
  } catch {
    return
  }
  selected.value = []
}

async function onSubmit() {
  const isValid = await formRef.value?.validate().catch(() => false)
  if (!isValid) return

  if (selected.value.length === 0) {
    ElMessage.error('请至少选择 1 台设备')
    return
  }

  saving.value = true
  try {
    const payload = {
      purpose: form.purpose.trim(),
      expected_return_date: form.expected_return_date ? (form.expected_return_date as string) : null,
      remark: form.remark.trim(),
      items: selected.value.map((e) => ({ equipment_id: e.id })),
    }
    const created = await createBorrowRequest(payload)
    ElMessage.success('已提交借用申请')
    await router.replace(`/borrow/${created.id}`)
  } catch (err: any) {
    const msg =
      err?.response?.data?.items ||
      err?.response?.data?.detail ||
      '提交失败，请检查设备是否仍可用'
    ElMessage.error(Array.isArray(msg) ? msg.join('; ') : String(msg))
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    await fetchCategories()
  } catch {
    // ignore
  }
  await fetchEquipmentList()
})
</script>

<template>
  <el-space direction="vertical" fill size="large">
    <el-card>
      <template #header>
        <div class="header">
          <div class="title">新建借用单</div>
          <div class="actions">
            <el-button @click="router.push('/borrow/requests')">返回列表</el-button>
            <el-button type="primary" :loading="saving" @click="onSubmit">提交申请</el-button>
          </div>
        </div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="用途" prop="purpose">
          <el-input v-model="form.purpose" placeholder="可选" />
        </el-form-item>
        <el-form-item label="预计归还" prop="expected_return_date">
          <el-date-picker
            v-model="form.expected_return_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="可选"
            style="width: 260px"
          />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <template #header>
        <div class="header">
          <div class="title">选择设备（仅显示 AVAILABLE）</div>
          <div class="actions">
            <el-button :disabled="selected.length === 0" @click="clearSelected">清空已选</el-button>
          </div>
        </div>
      </template>

      <el-form :inline="true" class="filters" @submit.prevent>
        <el-form-item label="分类">
          <el-select v-model="filters.categoryId" placeholder="全部" clearable filterable style="width: 220px">
            <el-option v-for="opt in categoryOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键字">
          <el-input
            v-model="filters.keyword"
            placeholder="按编码/名称搜索"
            clearable
            style="width: 240px"
            @keyup.enter="onSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-space>
            <el-button type="primary" @click="onSearch">查询</el-button>
            <el-button @click="onReset">重置</el-button>
          </el-space>
        </el-form-item>
      </el-form>

      <el-table v-loading="equipmentLoading" :data="equipmentList" stripe style="width: 100%">
        <el-table-column prop="code" label="编码" width="150" />
        <el-table-column prop="name" label="名称" min-width="220" />
        <el-table-column label="分类" width="200">
          <template #default="{ row }">
            <span>{{ row.category?.name }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="getEquipmentStatusTagType(row.status)">{{ getEquipmentStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="位置" width="160" />
        <el-table-column label="操作" width="140" align="right">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              :disabled="selectedIds.has(row.id)"
              @click="addEquipment(row)"
            >
              {{ selectedIds.has(row.id) ? '已添加' : '添加' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="equipmentPage"
          :page-size="equipmentPageSize"
          :total="equipmentTotal"
          layout="total, prev, pager, next"
          @current-change="fetchEquipmentList"
        />
      </div>
    </el-card>

    <el-card>
      <template #header>
        <div class="header">
          <div class="title">已选设备（{{ selected.length }}）</div>
        </div>
      </template>

      <el-table :data="selected" stripe style="width: 100%">
        <el-table-column prop="code" label="编码" width="150" />
        <el-table-column prop="name" label="名称" min-width="220" />
        <el-table-column label="分类" width="200">
          <template #default="{ row }">
            <span>{{ row.category?.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="位置" width="160" />
        <el-table-column label="操作" width="140" align="right">
          <template #default="{ row }">
            <el-button link type="danger" @click="removeEquipment(row.id)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="selected.length === 0" description="请从上方列表选择设备" />
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

.pagination {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>

