<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import {
  createEquipmentCategory,
  deleteEquipmentCategory,
  listEquipmentCategories,
  updateEquipmentCategory,
  type EquipmentCategory,
} from '../api/equipment'

const router = useRouter()

const loading = ref(false)
const categories = ref<EquipmentCategory[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

async function fetchCategories() {
  loading.value = true
  try {
    const data = await listEquipmentCategories({ page: page.value })
    categories.value = data.results
    total.value = data.count
    if (page.value === 1 && data.results.length) {
      pageSize.value = data.results.length
    }
  } finally {
    loading.value = false
  }
}

const dialogVisible = ref(false)
const saving = ref(false)
const editing = ref<EquipmentCategory | null>(null)
const formRef = ref<FormInstance>()
const formModel = reactive({
  code: '',
  name: '',
  description: '',
})

const rules: FormRules = {
  code: [{ required: true, message: '请输入分类编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }],
}

function openCreate() {
  editing.value = null
  formModel.code = ''
  formModel.name = ''
  formModel.description = ''
  dialogVisible.value = true
}

function openEdit(row: EquipmentCategory) {
  editing.value = row
  formModel.code = row.code
  formModel.name = row.name
  formModel.description = row.description || ''
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
      description: formModel.description?.trim() || '',
    }
    if (editing.value) {
      await updateEquipmentCategory(editing.value.id, payload)
    } else {
      await createEquipmentCategory(payload)
      page.value = 1
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await fetchCategories()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function onDelete(row: EquipmentCategory) {
  try {
    await ElMessageBox.confirm(`确认删除分类「${row.name}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }

  try {
    await deleteEquipmentCategory(row.id)
    ElMessage.success('已删除')
    if (categories.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    await fetchCategories()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '删除失败')
  }
}

onMounted(() => {
  void fetchCategories()
})
</script>

<template>
  <el-space direction="vertical" fill size="large">
    <el-card>
      <template #header>
        <div class="header">
          <div class="title">设备分类</div>
          <div class="actions">
            <el-button v-permission="'ADMIN'" type="primary" @click="openCreate">新增分类</el-button>
            <el-button @click="router.push('/equipment')">返回设备台账</el-button>
          </div>
        </div>
      </template>

      <el-table v-loading="loading" :data="categories" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="code" label="编码" width="160" />
        <el-table-column prop="name" label="名称" width="200" />
        <el-table-column prop="description" label="描述" min-width="240" />
        <el-table-column label="操作" width="180" align="right">
          <template #default="{ row }">
            <el-space>
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
          @current-change="fetchCategories"
        />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑分类' : '新增分类'" width="520px">
      <el-form ref="formRef" :model="formModel" :rules="rules" label-width="90px">
        <el-form-item label="编码" prop="code">
          <el-input v-model="formModel.code" placeholder="如 CHEM" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="formModel.name" placeholder="如 化学仪器" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="formModel.description" type="textarea" :rows="3" placeholder="可选" />
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

.pagination {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>

