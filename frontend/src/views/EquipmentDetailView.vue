<script setup lang="ts">
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { changeEquipmentStatus, fetchEquipment, fetchEquipmentLogs, type Equipment, type EquipmentStatusLog } from '../api/equipment'
import { EQUIPMENT_STATUS_OPTIONS, getEquipmentStatusLabel, getEquipmentStatusTagType } from '../constants/equipment'

const route = useRoute()
const router = useRouter()

const equipmentId = computed(() => Number(route.params.id))

const loading = ref(false)
const equipment = ref<Equipment | null>(null)
const logs = ref<EquipmentStatusLog[]>([])

async function fetchData() {
  if (!Number.isFinite(equipmentId.value)) return

  loading.value = true
  try {
    const [detail, statusLogs] = await Promise.all([
      fetchEquipment(equipmentId.value),
      fetchEquipmentLogs(equipmentId.value),
    ])
    equipment.value = detail
    logs.value = statusLogs
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

const statusDialogVisible = ref(false)
const saving = ref(false)
const statusFormRef = ref<FormInstance>()
const statusForm = reactive({
  to_status: '',
  reason: '',
  remark: '',
})

const statusRules: FormRules = {
  to_status: [{ required: true, message: '请选择目标状态', trigger: 'change' }],
}

const selectableStatusOptions = computed(() => {
  const current = equipment.value?.status
  return EQUIPMENT_STATUS_OPTIONS.filter((opt) => opt.value !== current)
})

function openStatusDialog() {
  statusForm.to_status = ''
  statusForm.reason = ''
  statusForm.remark = ''
  statusDialogVisible.value = true
}

async function onChangeStatus() {
  if (!statusFormRef.value || !equipment.value) return
  await statusFormRef.value.validate()

  saving.value = true
  try {
    await changeEquipmentStatus(equipment.value.id, {
      to_status: statusForm.to_status,
      reason: statusForm.reason?.trim() || '',
      remark: statusForm.remark?.trim() || '',
    })
    ElMessage.success('状态已更新')
    statusDialogVisible.value = false
    await fetchData()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.to_status?.[0] || err?.response?.data?.detail || '更新失败')
  } finally {
    saving.value = false
  }
}

watch(
  () => route.params.id,
  () => {
    void fetchData()
  },
)

onMounted(() => {
  void fetchData()
})
</script>

<template>
  <el-space direction="vertical" fill size="large">
    <el-card v-loading="loading">
      <template #header>
        <div class="header">
          <div class="title">设备详情</div>
          <div class="actions">
            <el-button v-permission="'ADMIN'" type="primary" @click="openStatusDialog">变更状态</el-button>
            <el-button @click="fetchData">刷新</el-button>
            <el-button @click="router.push('/equipment')">返回列表</el-button>
          </div>
        </div>
      </template>

      <el-descriptions v-if="equipment" :column="2" border>
        <el-descriptions-item label="编码">{{ equipment.code }}</el-descriptions-item>
        <el-descriptions-item label="名称">{{ equipment.name }}</el-descriptions-item>
        <el-descriptions-item label="分类">{{ equipment.category?.name }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getEquipmentStatusTagType(equipment.status)">{{ getEquipmentStatusLabel(equipment.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="位置">{{ equipment.location || '-' }}</el-descriptions-item>
        <el-descriptions-item label="可用">
          <el-tag :type="equipment.usable ? 'success' : 'info'">{{ equipment.usable ? '是' : '否' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="购置日期">{{ equipment.purchase_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="价格">{{ equipment.price ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="供应商">{{ equipment.vendor || '-' }}</el-descriptions-item>
        <el-descriptions-item label="规格">{{ equipment.spec || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ equipment.created_at }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ equipment.updated_at }}</el-descriptions-item>
      </el-descriptions>
      <el-empty v-else description="未找到设备" />
    </el-card>

    <el-card>
      <template #header>
        <div class="header">
          <div class="title">状态日志</div>
        </div>
      </template>

      <el-table v-if="logs.length" :data="logs" stripe style="width: 100%">
        <el-table-column prop="created_at" label="时间" width="180" />
        <el-table-column label="变更" width="220">
          <template #default="{ row }">
            <el-tag size="small" :type="getEquipmentStatusTagType(row.from_status)">
              {{ getEquipmentStatusLabel(row.from_status) }}
            </el-tag>
            <span class="arrow">→</span>
            <el-tag size="small" :type="getEquipmentStatusTagType(row.to_status)">
              {{ getEquipmentStatusLabel(row.to_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="changed_by_username" label="操作人" width="140" />
        <el-table-column prop="reason" label="原因" width="180" />
        <el-table-column prop="remark" label="备注" min-width="240" />
      </el-table>
      <el-empty v-else description="暂无日志" />
    </el-card>

    <el-dialog v-model="statusDialogVisible" title="变更设备状态" width="560px">
      <el-form ref="statusFormRef" :model="statusForm" :rules="statusRules" label-width="90px">
        <el-form-item label="目标状态" prop="to_status">
          <el-select v-model="statusForm.to_status" placeholder="请选择" style="width: 260px">
            <el-option v-for="opt in selectableStatusOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="原因">
          <el-input v-model="statusForm.reason" placeholder="可选" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="statusForm.remark" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-space>
          <el-button @click="statusDialogVisible = false">取消</el-button>
          <el-button v-permission="'ADMIN'" type="primary" :loading="saving" @click="onChangeStatus">
            提交
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

.arrow {
  margin: 0 8px;
  color: var(--el-text-color-secondary);
}
</style>

