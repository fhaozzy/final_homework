<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { listEquipment, type Equipment } from '../api/equipment'
import { createMaintenance, listMaintenance, patchMaintenance, type Maintenance, type MaintenanceStatus } from '../api/maintenance'
import { MAINTENANCE_STATUS_OPTIONS, getMaintenanceStatusLabel, getMaintenanceStatusTagType } from '../constants/maintenance'
import { getEquipmentStatusLabel } from '../constants/equipment'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const canWrite = computed(() => auth.hasAnyRole(['MAINTAINER', 'ADMIN']))

const filters = reactive({
  status: '' as '' | MaintenanceStatus,
  equipmentId: undefined as number | undefined,
  keyword: '',
})

const loading = ref(false)
const items = ref<Maintenance[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

async function fetchList() {
  loading.value = true
  try {
    const data = await listMaintenance({
      page: page.value,
      status: filters.status || undefined,
      equipment: filters.equipmentId || undefined,
      keyword: filters.keyword.trim() || undefined,
    })
    items.value = data.results
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
  void fetchList()
}

function onReset() {
  filters.status = ''
  filters.equipmentId = undefined
  filters.keyword = ''
  page.value = 1
  void fetchList()
}

// 设备搜索（用于筛选与创建）
type EquipmentOption = { id: number; label: string; status: string }
const equipmentSearching = ref(false)
const equipmentOptions = ref<EquipmentOption[]>([])

async function searchEquipment(query: string) {
  const keyword = query.trim()
  if (!keyword) {
    equipmentOptions.value = []
    return
  }

  equipmentSearching.value = true
  try {
    const data = await listEquipment({ page: 1, keyword })
    equipmentOptions.value = data.results.map((e: Equipment) => ({
      id: e.id,
      label: `${e.code} ${e.name}（${getEquipmentStatusLabel(e.status)}）`,
      status: e.status,
    }))
  } catch {
    equipmentOptions.value = []
  } finally {
    equipmentSearching.value = false
  }
}

function goEquipment(equipmentId: number) {
  router.push(`/equipment/${equipmentId}`)
}

// 创建维修单
const createDialogVisible = ref(false)
const creating = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive({
  equipmentId: undefined as number | undefined,
  title: '',
  description: '',
  cost: undefined as number | undefined,
})

const createRules: FormRules = {
  equipmentId: [{ required: true, message: '请选择设备', trigger: 'change' }],
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
}

function openCreate() {
  createForm.equipmentId = undefined
  createForm.title = ''
  createForm.description = ''
  createForm.cost = undefined
  createDialogVisible.value = true
}

async function onCreate() {
  if (!createFormRef.value) return
  await createFormRef.value.validate()

  creating.value = true
  try {
    await createMaintenance({
      equipment: createForm.equipmentId as number,
      title: createForm.title.trim(),
      description: createForm.description?.trim() || '',
      cost: createForm.cost ?? null,
    })
    ElMessage.success('维修单已创建（设备将进入维修状态）')
    createDialogVisible.value = false
    await fetchList()
  } catch (err: any) {
    const data = err?.response?.data
    const msg = data?.equipment || data?.detail || '创建失败'
    ElMessage.error(Array.isArray(msg) ? msg.join('; ') : String(msg))
  } finally {
    creating.value = false
  }
}

// 编辑（标题/描述/费用）
const editDialogVisible = ref(false)
const editing = ref(false)
const editFormRef = ref<FormInstance>()
const editingRow = ref<Maintenance | null>(null)
const editForm = reactive({
  title: '',
  description: '',
  cost: undefined as number | undefined,
})

const editRules: FormRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
}

function openEdit(row: Maintenance) {
  editingRow.value = row
  editForm.title = row.title || ''
  editForm.description = row.description || ''
  editForm.cost = row.cost != null && row.cost !== '' ? Number(row.cost) : undefined
  editDialogVisible.value = true
}

async function onSaveEdit() {
  if (!editFormRef.value || !editingRow.value) return
  await editFormRef.value.validate()

  editing.value = true
  try {
    await patchMaintenance(editingRow.value.id, {
      title: editForm.title.trim(),
      description: editForm.description?.trim() || '',
      cost: editForm.cost ?? null,
    })
    ElMessage.success('已更新')
    editDialogVisible.value = false
    await fetchList()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '更新失败')
  } finally {
    editing.value = false
  }
}

async function onStart(row: Maintenance) {
  try {
    await ElMessageBox.confirm(`确认开始维修「${row.title}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }

  try {
    await patchMaintenance(row.id, { status: 'IN_PROGRESS' })
    ElMessage.success('已进入处理中')
    await fetchList()
  } catch (err: any) {
    const data = err?.response?.data
    const msg = data?.status || data?.equipment || data?.detail || '操作失败'
    ElMessage.error(Array.isArray(msg) ? msg.join('; ') : String(msg))
  }
}

async function onDone(row: Maintenance) {
  try {
    await ElMessageBox.confirm('确认完成维修？完成后设备将恢复 AVAILABLE 并写入状态日志。', '提示', {
      type: 'warning',
    })
  } catch {
    return
  }

  try {
    await patchMaintenance(row.id, { status: 'DONE' })
    ElMessage.success('维修已完成，设备已恢复可用')
    await fetchList()
  } catch (err: any) {
    const data = err?.response?.data
    const msg = data?.status || data?.equipment || data?.detail || '操作失败'
    ElMessage.error(Array.isArray(msg) ? msg.join('; ') : String(msg))
  }
}

onMounted(() => {
  void fetchList()
})
</script>

<template>
  <el-space direction="vertical" fill size="large">
    <el-card>
      <template #header>
        <div class="header">
          <div class="title">维修单列表</div>
          <div class="actions">
            <el-button v-if="canWrite" type="primary" @click="openCreate">新建维修单</el-button>
            <el-button v-else disabled>仅管理员/维修员可新建</el-button>
          </div>
        </div>
      </template>

      <el-form :inline="true" class="filters" @submit.prevent>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 160px">
            <el-option v-for="opt in MAINTENANCE_STATUS_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>

        <el-form-item label="设备">
          <el-select
            v-model="filters.equipmentId"
            placeholder="输入设备编码/名称搜索"
            clearable
            filterable
            remote
            :remote-method="searchEquipment"
            :loading="equipmentSearching"
            style="width: 260px"
          >
            <el-option
              v-for="opt in equipmentOptions"
              :key="opt.id"
              :label="opt.label"
              :value="opt.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="关键字">
          <el-input
            v-model="filters.keyword"
            placeholder="标题/描述"
            clearable
            style="width: 220px"
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

      <el-table v-loading="loading" :data="items" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="90" />
        <el-table-column label="设备" min-width="220">
          <template #default="{ row }">
            <el-button link type="primary" @click="goEquipment(row.equipment_id)">
              {{ row.equipment_code }} {{ row.equipment_name }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="220" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getMaintenanceStatusTagType(row.status)">{{ getMaintenanceStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="assigned_to_username" label="指派" width="140" />
        <el-table-column label="费用" width="120" align="right">
          <template #default="{ row }">
            <span>{{ row.cost ?? '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="180" />
        <el-table-column prop="finished_at" label="完成时间" width="180" />
        <el-table-column label="操作" width="240" align="right">
          <template #default="{ row }">
            <el-space>
              <el-button v-if="canWrite" link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button
                v-if="canWrite && row.status === 'OPEN'"
                link
                type="warning"
                @click="onStart(row)"
              >
                开始
              </el-button>
              <el-button
                v-if="canWrite && row.status === 'IN_PROGRESS'"
                link
                type="success"
                @click="onDone(row)"
              >
                完成
              </el-button>
              <el-button link type="info" @click="goEquipment(row.equipment_id)">设备详情</el-button>
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
          @current-change="fetchList"
        />
      </div>
    </el-card>

    <el-dialog v-model="createDialogVisible" title="新建维修单" width="720px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="90px">
        <el-form-item label="设备" prop="equipmentId">
          <el-select
            v-model="createForm.equipmentId"
            placeholder="输入设备编码/名称搜索"
            filterable
            remote
            :remote-method="searchEquipment"
            :loading="equipmentSearching"
            style="width: 420px"
          >
            <el-option
              v-for="opt in equipmentOptions"
              :key="opt.id"
              :label="opt.label"
              :value="opt.id"
              :disabled="!['AVAILABLE', 'MAINTENANCE'].includes(opt.status)"
            />
          </el-select>
          <el-tag class="ml-8" type="info">仅 AVAILABLE/MAINTENANCE 可建单</el-tag>
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input v-model="createForm.title" placeholder="如：更换探头" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
        <el-form-item label="费用">
          <el-input-number v-model="createForm.cost" :min="0" :precision="2" style="width: 220px" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-space>
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="creating" @click="onCreate">创建</el-button>
        </el-space>
      </template>
    </el-dialog>

    <el-dialog v-model="editDialogVisible" title="编辑维修单" width="720px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="90px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="费用">
          <el-input-number v-model="editForm.cost" :min="0" :precision="2" style="width: 220px" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-space>
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="editing" @click="onSaveEdit">保存</el-button>
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

.ml-8 {
  margin-left: 8px;
}
</style>
