<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import {
  createEquipment,
  deleteEquipment,
  fetchAllEquipmentCategories,
  listEquipment,
  updateEquipment,
  type Equipment,
  type EquipmentCategory,
} from '../api/equipment'
import { EQUIPMENT_STATUS_OPTIONS, getEquipmentStatusLabel, getEquipmentStatusTagType } from '../constants/equipment'

const router = useRouter()

const loading = ref(false)
const equipmentList = ref<Equipment[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

const categories = ref<EquipmentCategory[]>([])

const filters = reactive({
  status: '',
  categoryId: undefined as number | undefined,
  keyword: '',
})

const categoryOptions = computed(() => categories.value.map((c) => ({ label: `${c.name}(${c.code})`, value: c.id })))

async function fetchCategories() {
  categories.value = await fetchAllEquipmentCategories()
}

async function fetchEquipmentList() {
  loading.value = true
  try {
    const data = await listEquipment({
      page: page.value,
      status: filters.status || undefined,
      category: filters.categoryId || undefined,
      keyword: filters.keyword.trim() || undefined,
    })
    equipmentList.value = data.results
    total.value = data.count
    if (page.value === 1 && data.results.length) {
      pageSize.value = data.results.length
    }
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  void fetchEquipmentList()
}

function onReset() {
  filters.status = ''
  filters.categoryId = undefined
  filters.keyword = ''
  page.value = 1
  void fetchEquipmentList()
}

const dialogVisible = ref(false)
const saving = ref(false)
const editing = ref<Equipment | null>(null)
const formRef = ref<FormInstance>()

const formModel = reactive({
  code: '',
  name: '',
  category_id: undefined as number | undefined,
  status: 'AVAILABLE',
  location: '',
  purchase_date: '' as string | '',
  price: undefined as number | undefined,
  vendor: '',
  spec: '',
  usable: true,
})

const rules: FormRules = {
  code: [{ required: true, message: '请输入设备编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],
}

function resetForm() {
  formModel.code = ''
  formModel.name = ''
  formModel.category_id = undefined
  formModel.status = 'AVAILABLE'
  formModel.location = ''
  formModel.purchase_date = ''
  formModel.price = undefined
  formModel.vendor = ''
  formModel.spec = ''
  formModel.usable = true
}

function openCreate() {
  editing.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Equipment) {
  editing.value = row
  formModel.code = row.code
  formModel.name = row.name
  formModel.category_id = row.category?.id
  formModel.status = row.status
  formModel.location = row.location || ''
  formModel.purchase_date = row.purchase_date || ''
  formModel.price = row.price != null && row.price !== '' ? Number(row.price) : undefined
  formModel.vendor = row.vendor || ''
  formModel.spec = row.spec || ''
  formModel.usable = Boolean(row.usable)
  dialogVisible.value = true
}

async function onSave() {
  if (!formRef.value) return
  await formRef.value.validate()

  saving.value = true
  try {
    const payload = {
      code: formModel.code.trim(),
      name: formModel.name.trim(),
      category_id: formModel.category_id as number,
      status: formModel.status,
      location: formModel.location?.trim() || '',
      purchase_date: formModel.purchase_date ? (formModel.purchase_date as string) : null,
      price: formModel.price ?? null,
      vendor: formModel.vendor?.trim() || '',
      spec: formModel.spec?.trim() || '',
      usable: formModel.usable,
    }

    if (editing.value) {
      await updateEquipment(editing.value.id, payload)
    } else {
      await createEquipment(payload)
      page.value = 1
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await fetchEquipmentList()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function onDelete(row: Equipment) {
  try {
    await ElMessageBox.confirm(`确认删除设备「${row.name}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }

  try {
    await deleteEquipment(row.id)
    ElMessage.success('已删除')
    if (equipmentList.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    await fetchEquipmentList()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '删除失败')
  }
}

function goDetail(row: Equipment) {
  router.push(`/equipment/${row.id}`)
}

onMounted(async () => {
  try {
    await fetchCategories()
  } catch {
    // ignore categories loading errors in list page
  }
  await fetchEquipmentList()
})
</script>

<template>
  <el-space direction="vertical" fill size="large">
    <el-card>
      <template #header>
        <div class="header">
          <div class="title">设备台账</div>
          <div class="actions">
            <el-button v-permission="'ADMIN'" type="primary" @click="openCreate">新增设备</el-button>
            <el-button v-permission="'ADMIN'" @click="router.push('/equipment/categories')">分类管理</el-button>
          </div>
        </div>
      </template>

      <el-form :inline="true" class="filters" @submit.prevent>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 160px">
            <el-option v-for="opt in EQUIPMENT_STATUS_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>

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

      <el-table v-loading="loading" :data="equipmentList" stripe style="width: 100%">
        <el-table-column prop="code" label="编码" width="150" />
        <el-table-column prop="name" label="名称" min-width="200" />
        <el-table-column label="分类" width="200">
          <template #default="{ row }">
            <span>{{ row.category?.name }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="140">
          <template #default="{ row }">
            <el-tag :type="getEquipmentStatusTagType(row.status)">{{ getEquipmentStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="位置" width="160" />
        <el-table-column label="可用" width="90">
          <template #default="{ row }">
            <el-tag :type="row.usable ? 'success' : 'info'">{{ row.usable ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" align="right">
          <template #default="{ row }">
            <el-space>
              <el-button link type="primary" @click="goDetail(row)">详情</el-button>
              <el-button v-permission="'ADMIN'" link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button v-permission="'ADMIN'" link type="danger" @click="onDelete(row)">删除</el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchEquipmentList"
        />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑设备' : '新增设备'" width="720px">
      <el-form ref="formRef" :model="formModel" :rules="rules" label-width="90px">
        <el-form-item label="编码" prop="code">
          <el-input v-model="formModel.code" placeholder="如 EQ-001" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="formModel.name" placeholder="如 示波器" />
        </el-form-item>
        <el-form-item label="分类" prop="category_id">
          <el-select v-model="formModel.category_id" placeholder="请选择" filterable style="width: 260px">
            <el-option v-for="opt in categoryOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="formModel.status" style="width: 260px">
            <el-option v-for="opt in EQUIPMENT_STATUS_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="位置" prop="location">
          <el-input v-model="formModel.location" placeholder="可选" />
        </el-form-item>
        <el-form-item label="购置日期" prop="purchase_date">
          <el-date-picker
            v-model="formModel.purchase_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="可选"
            style="width: 260px"
          />
        </el-form-item>
        <el-form-item label="价格" prop="price">
          <el-input-number v-model="formModel.price" :min="0" :precision="2" :step="100" style="width: 260px" />
        </el-form-item>
        <el-form-item label="供应商" prop="vendor">
          <el-input v-model="formModel.vendor" placeholder="可选" />
        </el-form-item>
        <el-form-item label="规格" prop="spec">
          <el-input v-model="formModel.spec" placeholder="可选" />
        </el-form-item>
        <el-form-item label="可用" prop="usable">
          <el-switch v-model="formModel.usable" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-space>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button v-permission="'ADMIN'" type="primary" :loading="saving" @click="onSave">
            保存
          </el-button>
        </el-space>
      </template>
    </el-dialog>
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
