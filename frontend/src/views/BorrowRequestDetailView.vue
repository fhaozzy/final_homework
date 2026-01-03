<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  approveBorrowRequest,
  checkoutBorrowRequest,
  fetchBorrowRequest,
  rejectBorrowRequest,
  returnBorrowRequest,
  submitReturnRequest,
  type BorrowRequest,
  type ReturnCondition,
} from '../api/borrowing'
import { getBorrowItemStatusLabel, getBorrowItemStatusTagType, getBorrowRequestStatusLabel, getBorrowRequestStatusTagType } from '../constants/borrowing'
import { getEquipmentStatusLabel, getEquipmentStatusTagType } from '../constants/equipment'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const requestId = computed(() => Number(route.params.id))

const loading = ref(false)
const detail = ref<BorrowRequest | null>(null)

async function fetchDetail() {
  if (!Number.isFinite(requestId.value)) return
  loading.value = true
  try {
    detail.value = await fetchBorrowRequest(requestId.value)
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

const canOperate = computed(() => auth.isAdmin)

// 学生是否可以提交归还申请
const canSubmitReturn = computed(() => {
  if (!detail.value) return false
  // 只有申请人可以提交归还申请
  if (detail.value.applicant !== auth.user?.id) return false
  // 只有状态为 OUT 时才能提交归还申请
  return detail.value.status === 'OUT'
})

// 管理员是否可以验收归还
const canAcceptReturn = computed(() => {
  if (!detail.value) return false
  if (!auth.isAdmin) return false
  // 只有状态为 OUT 且有 RETURN_PENDING 的项时才能验收
  if (detail.value.status !== 'OUT') return false
  return detail.value.items?.some((it) => it.status === 'RETURN_PENDING')
})

const commentDialogVisible = ref(false)
const commentMode = ref<'approve' | 'reject'>('approve')
const commentSaving = ref(false)
const commentFormRef = ref<FormInstance>()
const commentForm = reactive({
  comment: '',
})

const commentRules: FormRules = {
  comment: [{ required: false }],
}

function openCommentDialog(mode: 'approve' | 'reject') {
  commentMode.value = mode
  commentForm.comment = ''
  commentDialogVisible.value = true
}

async function submitCommentAction() {
  if (!detail.value) return
  const isValid = await commentFormRef.value?.validate().catch(() => false)
  if (!isValid) return

  commentSaving.value = true
  try {
    const payload = { comment: commentForm.comment.trim() }
    if (commentMode.value === 'approve') {
      await approveBorrowRequest(detail.value.id, payload)
      ElMessage.success('已审批通过')
    } else {
      await rejectBorrowRequest(detail.value.id, payload)
      ElMessage.success('已拒绝')
    }
    commentDialogVisible.value = false
    await fetchDetail()
  } catch (err: any) {
    const msg =
      err?.response?.data?.detail ||
      err?.response?.data?.status ||
      err?.response?.data?.approval ||
      '操作失败'
    ElMessage.error(Array.isArray(msg) ? msg.join('; ') : String(msg))
  } finally {
    commentSaving.value = false
  }
}

async function onCheckout() {
  if (!detail.value) return
  try {
    await ElMessageBox.confirm('确认出库？（将锁定并更新设备状态）', '提示', { type: 'warning' })
  } catch {
    return
  }

  try {
    await checkoutBorrowRequest(detail.value.id)
    ElMessage.success('已出库')
    await fetchDetail()
  } catch (err: any) {
    const msg = err?.response?.data?.detail || err?.response?.data?.equipment || '出库失败'
    ElMessage.error(Array.isArray(msg) ? msg.join('; ') : String(msg))
  }
}

async function onSubmitReturn() {
  if (!detail.value) return
  try {
    await ElMessageBox.confirm('确认提交归还申请？', '提示', { type: 'warning' })
  } catch {
    return
  }

  try {
    await submitReturnRequest(detail.value.id)
    ElMessage.success('已提交归还申请，等待管理员验收')
    await fetchDetail()
  } catch (err: any) {
    const msg = err?.response?.data?.detail || err?.response?.data?.status || '提交失败'
    ElMessage.error(Array.isArray(msg) ? msg.join('; ') : String(msg))
  }
}

const returnDialogVisible = ref(false)
const returnSaving = ref(false)
type ReturnItemForm = {
  borrow_item_id: number
  equipment_code: string
  equipment_name: string
  condition: ReturnCondition
  fee: number
  remark: string
}
const returnItems = ref<ReturnItemForm[]>([])

const conditionOptions: Array<{ value: ReturnCondition; label: string }> = [
  { value: 'GOOD', label: '完好' },
  { value: 'DAMAGED', label: '损坏' },
  { value: 'LOST', label: '丢失' },
]

function openReturnDialog() {
  if (!detail.value) return
  returnItems.value = (detail.value.items || [])
    .filter((it) => it.item_type === 'EQUIPMENT' && it.equipment && it.status === 'RETURN_PENDING')
    .map((it) => ({
      borrow_item_id: it.id,
      equipment_code: it.equipment?.code || '-',
      equipment_name: it.equipment?.name || '-',
      condition: 'GOOD' as ReturnCondition,
      fee: 0,
      remark: '',
    }))
  returnDialogVisible.value = true
}

async function submitReturn() {
  if (!detail.value) return
  returnSaving.value = true
  try {
    await returnBorrowRequest(detail.value.id, {
      items: returnItems.value.map((it) => ({
        borrow_item_id: it.borrow_item_id,
        condition: it.condition,
        fee: it.fee,
        remark: it.remark?.trim() || '',
      })),
    })
    ElMessage.success('已归还验收')
    returnDialogVisible.value = false
    await fetchDetail()
  } catch (err: any) {
    const msg = err?.response?.data?.detail || err?.response?.data?.status || '归还失败'
    ElMessage.error(Array.isArray(msg) ? msg.join('; ') : String(msg))
  } finally {
    returnSaving.value = false
  }
}

watch(
  () => route.params.id,
  () => {
    void fetchDetail()
  },
)

onMounted(() => {
  void fetchDetail()
})
</script>

<template>
  <el-space direction="vertical" fill size="large">
    <el-card v-loading="loading">
      <template #header>
        <div class="header">
          <div class="title">借用单详情 #{{ requestId }}</div>
          <div class="actions">
            <el-button @click="fetchDetail">刷新</el-button>
            <el-button @click="router.push('/borrow/requests')">返回列表</el-button>
          </div>
        </div>
      </template>

      <el-descriptions v-if="detail" :column="2" border>
        <el-descriptions-item label="状态">
          <el-tag :type="getBorrowRequestStatusTagType(detail.status)">{{ getBorrowRequestStatusLabel(detail.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="申请人">{{ detail.applicant_username }}</el-descriptions-item>
        <el-descriptions-item label="用途">{{ detail.purpose || '-' }}</el-descriptions-item>
        <el-descriptions-item label="预计归还">{{ detail.expected_return_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ detail.remark || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ detail.created_at }}</el-descriptions-item>
        <el-descriptions-item label="提交时间">{{ detail.submitted_at || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审批人">{{ detail.approver_username || '-' }}</el-descriptions-item>
        <el-descriptions-item label="通过时间">{{ detail.approved_at || '-' }}</el-descriptions-item>
        <el-descriptions-item label="拒绝时间">{{ detail.rejected_at || '-' }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ detail.updated_at }}</el-descriptions-item>
      </el-descriptions>
      <el-empty v-else description="未找到借用单" />
    </el-card>

    <el-card v-if="detail">
      <template #header>
        <div class="header">
          <div class="title">流程操作</div>
          <div class="hint" v-if="!canOperate">仅管理员可操作（老师/学生只读）</div>
        </div>
      </template>

      <el-space>
        <el-button
          v-if="detail.status === 'REQUESTED'"
          type="success"
          :disabled="!canOperate"
          @click="openCommentDialog('approve')"
        >
          审批通过
        </el-button>
        <el-button
          v-if="detail.status === 'REQUESTED'"
          type="danger"
          :disabled="!canOperate"
          @click="openCommentDialog('reject')"
        >
          审批拒绝
        </el-button>
        <el-button
          v-if="detail.status === 'APPROVED'"
          type="warning"
          :disabled="!canOperate"
          @click="onCheckout"
        >
          出库
        </el-button>
        <el-button
          v-if="canSubmitReturn"
          type="primary"
          @click="onSubmitReturn"
        >
          提交归还申请
        </el-button>
        <el-button
          v-if="canAcceptReturn"
          type="primary"
          :disabled="!canOperate"
          @click="openReturnDialog"
        >
          归还验收
        </el-button>
      </el-space>
    </el-card>

    <el-card v-if="detail">
      <template #header>
        <div class="header">
          <div class="title">设备明细</div>
        </div>
      </template>

      <el-table :data="detail.items" stripe style="width: 100%">
        <el-table-column prop="equipment.code" label="设备编码" width="150" />
        <el-table-column prop="equipment.name" label="设备名称" min-width="220" />
        <el-table-column label="设备状态" width="140">
          <template #default="{ row }">
            <el-tag v-if="row.equipment" size="small" :type="getEquipmentStatusTagType(row.equipment.status)">
              {{ getEquipmentStatusLabel(row.equipment.status) }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="行状态" width="140">
          <template #default="{ row }">
            <el-tag size="small" :type="getBorrowItemStatusTagType(row.status)">{{ getBorrowItemStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="out_at" label="出库时间" width="180" />
        <el-table-column prop="return_checked_at" label="验收时间" width="180" />
      </el-table>
    </el-card>

    <el-card v-if="detail && detail.approval">
      <template #header>
        <div class="header">
          <div class="title">审批记录</div>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="决策">{{ detail.approval.decision }}</el-descriptions-item>
        <el-descriptions-item label="审批人">{{ detail.approval.approver_username }}</el-descriptions-item>
        <el-descriptions-item label="审批时间">{{ detail.approval.decided_at }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ detail.approval.comment || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-dialog v-model="commentDialogVisible" :title="commentMode === 'approve' ? '审批通过' : '审批拒绝'" width="520px">
      <el-form ref="commentFormRef" :model="commentForm" :rules="commentRules" label-width="90px">
        <el-form-item label="备注" prop="comment">
          <el-input v-model="commentForm.comment" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-space>
          <el-button @click="commentDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="commentSaving" @click="submitCommentAction">提交</el-button>
        </el-space>
      </template>
    </el-dialog>

    <el-dialog v-model="returnDialogVisible" title="归还验收" width="860px">
      <el-alert title="可为每台设备填写验收结果；不填写默认“完好/0元”。" type="info" show-icon class="mb-12" />

      <el-table :data="returnItems" stripe style="width: 100%">
        <el-table-column prop="equipment_code" label="设备编码" width="160" />
        <el-table-column prop="equipment_name" label="设备名称" min-width="200" />
        <el-table-column label="验收结果" width="160">
          <template #default="{ row }">
            <el-select v-model="row.condition" style="width: 130px">
              <el-option v-for="opt in conditionOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="费用" width="160">
          <template #default="{ row }">
            <el-input-number v-model="row.fee" :min="0" :precision="2" style="width: 140px" />
          </template>
        </el-table-column>
        <el-table-column label="备注" min-width="220">
          <template #default="{ row }">
            <el-input v-model="row.remark" placeholder="可选" />
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-space>
          <el-button @click="returnDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="returnSaving" @click="submitReturn">提交验收</el-button>
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

.hint {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.mb-12 {
  margin-bottom: 12px;
}
</style>

