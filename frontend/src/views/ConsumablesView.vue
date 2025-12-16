<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { computed, onMounted, reactive, ref, watch } from 'vue'

import {
  createConsumable,
  deleteConsumable,
  fetchAllConsumables,
  listConsumables,
  listConsumableWarnings,
  updateConsumable,
  type Consumable,
} from '../api/consumables'
import { approveStockTxn, listStockTxns, rejectStockTxn, stockIn, stockOut, type StockTxn } from '../api/stock'
import { getStockTxnStatusLabel, getStockTxnStatusTagType, getStockTxnTypeLabel, getStockTxnTypeTagType } from '../constants/stock'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

const activeTab = ref<'consumables' | 'warnings' | 'stock-in' | 'stock-out' | 'txns'>('consumables')

const isAdmin = computed(() => auth.isAdmin)

// 1) 耗材台账
const loading = ref(false)
const consumables = ref<Consumable[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

async function fetchConsumables() {
  loading.value = true
  try {
    const data = await listConsumables({ page: page.value })
    consumables.value = data.results
    total.value = data.count
    if (page.value === 1 && data.results.length) {
      pageSize.value = data.results.length
    }
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '加载耗材失败')
  } finally {
    loading.value = false
  }
}

function isWarningRow(row: Consumable): boolean {
  return row.current_qty < row.safety_stock
}

const dialogVisible = ref(false)
const saving = ref(false)
const editing = ref<Consumable | null>(null)
const formRef = ref<FormInstance>()
const formModel = reactive({
  code: '',
  name: '',
  unit: '',
  category: '',
  safety_stock: 0,
  location: '',
})

const rules: FormRules = {
  code: [{ required: true, message: '请输入耗材编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入耗材名称', trigger: 'blur' }],
  unit: [{ required: true, message: '请输入单位', trigger: 'blur' }],
}

function openCreate() {
  editing.value = null
  formModel.code = ''
  formModel.name = ''
  formModel.unit = ''
  formModel.category = ''
  formModel.safety_stock = 0
  formModel.location = ''
  dialogVisible.value = true
}

function openEdit(row: Consumable) {
  editing.value = row
  formModel.code = row.code
  formModel.name = row.name
  formModel.unit = row.unit
  formModel.category = row.category || ''
  formModel.safety_stock = row.safety_stock ?? 0
  formModel.location = row.location || ''
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
      unit: formModel.unit.trim(),
      category: formModel.category?.trim() || '',
      safety_stock: Number.isFinite(formModel.safety_stock) ? formModel.safety_stock : 0,
      location: formModel.location?.trim() || '',
    }
    if (editing.value) {
      await updateConsumable(editing.value.id, payload)
    } else {
      await createConsumable(payload)
      page.value = 1
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await fetchConsumables()
    await refreshWarningsSilently()
    await refreshAllConsumablesSilently()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function onDelete(row: Consumable) {
  try {
    await ElMessageBox.confirm(`确认删除耗材「${row.name}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }

  try {
    await deleteConsumable(row.id)
    ElMessage.success('已删除')
    if (consumables.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    await fetchConsumables()
    await refreshWarningsSilently()
    await refreshAllConsumablesSilently()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '删除失败')
  }
}

// 2) 预警列表
const warningsLoading = ref(false)
const warnings = ref<Consumable[]>([])

async function fetchWarnings() {
  warningsLoading.value = true
  try {
    warnings.value = await listConsumableWarnings()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '加载预警失败')
  } finally {
    warningsLoading.value = false
  }
}

async function refreshWarningsSilently() {
  try {
    warnings.value = await listConsumableWarnings()
  } catch {
    // ignore
  }
}

// 3) 入库/领用表单：需要耗材下拉
const allConsumables = ref<Consumable[]>([])
const consumableOptions = computed(() =>
  allConsumables.value.map((c) => ({
    label: `${c.name}(${c.code}) - 库存:${c.current_qty}`,
    value: c.id,
  })),
)

async function refreshAllConsumables() {
  allConsumables.value = await fetchAllConsumables()
}

async function refreshAllConsumablesSilently() {
  try {
    allConsumables.value = await fetchAllConsumables()
  } catch {
    // ignore
  }
}

const stockInRef = ref<FormInstance>()
const stockInForm = reactive({
  consumable_id: undefined as number | undefined,
  qty: 1,
  remark: '',
})
const stockInRules: FormRules = {
  consumable_id: [{ required: true, message: '请选择耗材', trigger: 'change' }],
  qty: [{ required: true, message: '请输入数量', trigger: 'blur' }],
}
const stockInSubmitting = ref(false)

async function onStockIn() {
  if (!stockInRef.value) return
  await stockInRef.value.validate()

  stockInSubmitting.value = true
  try {
    await stockIn({
      consumable_id: stockInForm.consumable_id as number,
      qty: stockInForm.qty,
      remark: stockInForm.remark?.trim() || '',
    })
    ElMessage.success('入库成功')
    stockInForm.qty = 1
    stockInForm.remark = ''
    await fetchConsumables()
    await refreshAllConsumables()
    await refreshWarningsSilently()
    await fetchTxns()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '入库失败')
  } finally {
    stockInSubmitting.value = false
  }
}

const stockOutRef = ref<FormInstance>()
const stockOutForm = reactive({
  consumable_id: undefined as number | undefined,
  qty: 1,
  remark: '',
})
const stockOutRules: FormRules = {
  consumable_id: [{ required: true, message: '请选择耗材', trigger: 'change' }],
  qty: [{ required: true, message: '请输入数量', trigger: 'blur' }],
}
const stockOutSubmitting = ref(false)

async function onStockOut() {
  if (!stockOutRef.value) return
  await stockOutRef.value.validate()

  stockOutSubmitting.value = true
  try {
    await stockOut({
      consumable_id: stockOutForm.consumable_id as number,
      qty: stockOutForm.qty,
      remark: stockOutForm.remark?.trim() || '',
    })
    ElMessage.success('已提交领用申请（待管理员审核）')
    stockOutForm.qty = 1
    stockOutForm.remark = ''
    await fetchTxns()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '提交失败')
  } finally {
    stockOutSubmitting.value = false
  }
}

// 4) 库存流水
const txnsLoading = ref(false)
const txns = ref<StockTxn[]>([])
const txnTotal = ref(0)
const txnPage = ref(1)
const txnPageSize = ref(10)

async function fetchTxns() {
  txnsLoading.value = true
  try {
    const data = await listStockTxns({ page: txnPage.value })
    txns.value = data.results
    txnTotal.value = data.count
    if (txnPage.value === 1 && data.results.length) {
      txnPageSize.value = data.results.length
    }
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '加载流水失败')
  } finally {
    txnsLoading.value = false
  }
}

const canReviewTxn = computed(() => auth.isAdmin)

async function onApproveTxn(row: StockTxn) {
  try {
    await ElMessageBox.confirm(`确认通过领用申请「${row.consumable_name}」数量 ${row.qty}？`, '提示', {
      type: 'warning',
    })
  } catch {
    return
  }

  try {
    await approveStockTxn(row.id)
    ElMessage.success('已通过')
    await fetchTxns()
    await fetchConsumables()
    await refreshAllConsumablesSilently()
    await refreshWarningsSilently()
  } catch (err: any) {
    const data = err?.response?.data
    const msg = data?.stock || data?.detail || '审批失败（可能库存不足）'
    ElMessage.error(Array.isArray(msg) ? msg.join('; ') : String(msg))
  }
}

async function onRejectTxn(row: StockTxn) {
  try {
    await ElMessageBox.confirm(`确认拒绝领用申请「${row.consumable_name}」数量 ${row.qty}？`, '提示', {
      type: 'warning',
    })
  } catch {
    return
  }

  try {
    await rejectStockTxn(row.id)
    ElMessage.success('已拒绝')
    await fetchTxns()
  } catch (err: any) {
    const data = err?.response?.data
    const msg = data?.detail || '拒绝失败'
    ElMessage.error(Array.isArray(msg) ? msg.join('; ') : String(msg))
  }
}

watch(
  () => activeTab.value,
  (tab) => {
    if (tab === 'warnings' && warnings.value.length === 0) {
      void fetchWarnings()
    }
    if ((tab === 'stock-in' || tab === 'stock-out') && allConsumables.value.length === 0) {
      void refreshAllConsumables()
    }
    if (tab === 'txns' && txns.value.length === 0) {
      void fetchTxns()
    }
  },
)

onMounted(async () => {
  await fetchConsumables()
  await refreshAllConsumablesSilently()
})
</script>

<template>
  <el-space direction="vertical" fill size="large">
    <el-card>
      <template #header>
        <div class="header">
          <div class="title">耗材与库存</div>
          <div class="actions">
            <el-button @click="fetchConsumables">刷新台账</el-button>
            <el-button @click="fetchTxns">刷新流水</el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="耗材台账" name="consumables">
          <div class="pane-header">
            <el-button v-permission="'ADMIN'" type="primary" @click="openCreate">新增耗材</el-button>
          </div>

          <el-table v-loading="loading" :data="consumables" stripe style="width: 100%">
            <el-table-column prop="code" label="编码" width="160" />
            <el-table-column prop="name" label="名称" min-width="200" />
            <el-table-column prop="category" label="分类" width="160" />
            <el-table-column prop="unit" label="单位" width="100" />
            <el-table-column label="库存" width="120" align="right">
              <template #default="{ row }">
                <el-tag :type="isWarningRow(row) ? 'danger' : 'success'">{{ row.current_qty }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="safety_stock" label="安全库存" width="120" align="right" />
            <el-table-column prop="location" label="位置" width="160" />
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
              @current-change="fetchConsumables"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="预警列表" name="warnings">
          <div class="pane-header">
            <el-button @click="fetchWarnings">刷新预警</el-button>
          </div>
          <el-table v-loading="warningsLoading" :data="warnings" stripe style="width: 100%">
            <el-table-column prop="code" label="编码" width="160" />
            <el-table-column prop="name" label="名称" min-width="220" />
            <el-table-column prop="category" label="分类" width="160" />
            <el-table-column prop="unit" label="单位" width="100" />
            <el-table-column label="库存" width="120" align="right">
              <template #default="{ row }">
                <el-tag type="danger">{{ row.current_qty }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="safety_stock" label="安全库存" width="120" align="right" />
            <el-table-column prop="location" label="位置" width="160" />
          </el-table>
          <el-empty v-if="!warningsLoading && warnings.length === 0" description="暂无预警" />
        </el-tab-pane>

        <el-tab-pane label="入库" name="stock-in" :disabled="!isAdmin">
          <el-alert
            v-if="!isAdmin"
            title="仅管理员可入库"
            type="warning"
            show-icon
            class="mb-12"
          />
          <el-form ref="stockInRef" :model="stockInForm" :rules="stockInRules" label-width="90px" class="form">
            <el-form-item label="耗材" prop="consumable_id">
              <el-select v-model="stockInForm.consumable_id" filterable placeholder="请选择" style="width: 420px">
                <el-option v-for="opt in consumableOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="数量" prop="qty">
              <el-input-number v-model="stockInForm.qty" :min="1" style="width: 220px" />
            </el-form-item>
            <el-form-item label="备注">
              <el-input v-model="stockInForm.remark" placeholder="可选" style="width: 420px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="stockInSubmitting" :disabled="!isAdmin" @click="onStockIn">
                提交入库
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="领用申请" name="stock-out">
          <el-form ref="stockOutRef" :model="stockOutForm" :rules="stockOutRules" label-width="90px" class="form">
            <el-form-item label="耗材" prop="consumable_id">
              <el-select v-model="stockOutForm.consumable_id" filterable placeholder="请选择" style="width: 420px">
                <el-option v-for="opt in consumableOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="数量" prop="qty">
              <el-input-number v-model="stockOutForm.qty" :min="1" style="width: 220px" />
            </el-form-item>
            <el-form-item label="用途/备注">
              <el-input v-model="stockOutForm.remark" placeholder="可选" style="width: 420px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="stockOutSubmitting" @click="onStockOut">
                提交申请
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="库存流水" name="txns">
          <div class="pane-header">
            <el-button @click="fetchTxns">刷新流水</el-button>
          </div>
          <el-table v-loading="txnsLoading" :data="txns" stripe style="width: 100%">
            <el-table-column prop="id" label="ID" width="90" />
            <el-table-column prop="consumable_name" label="耗材" min-width="220" />
            <el-table-column label="类型" width="110">
              <template #default="{ row }">
                <el-tag size="small" :type="getStockTxnTypeTagType(row.type)">{{ getStockTxnTypeLabel(row.type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag size="small" :type="getStockTxnStatusTagType(row.status)">{{ getStockTxnStatusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="qty" label="数量" width="110" align="right" />
            <el-table-column prop="performed_by_username" label="申请人" width="140" />
            <el-table-column prop="reviewed_by_username" label="审核人" width="140" />
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column label="操作" width="200" align="right">
              <template #default="{ row }">
                <el-space>
                  <el-button
                    v-if="canReviewTxn && row.type === 'OUT' && row.status === 'PENDING'"
                    link
                    type="success"
                    @click="onApproveTxn(row)"
                  >
                    通过
                  </el-button>
                  <el-button
                    v-if="canReviewTxn && row.type === 'OUT' && row.status === 'PENDING'"
                    link
                    type="danger"
                    @click="onRejectTxn(row)"
                  >
                    拒绝
                  </el-button>
                  <span v-if="!(canReviewTxn && row.type === 'OUT' && row.status === 'PENDING')">-</span>
                </el-space>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination">
            <el-pagination
              v-model:current-page="txnPage"
              :page-size="txnPageSize"
              :total="txnTotal"
              layout="total, prev, pager, next"
              @current-change="fetchTxns"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑耗材' : '新增耗材'" width="640px">
      <el-form ref="formRef" :model="formModel" :rules="rules" label-width="90px">
        <el-form-item label="编码" prop="code">
          <el-input v-model="formModel.code" placeholder="如 C-001" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="formModel.name" placeholder="如 一次性手套" />
        </el-form-item>
        <el-form-item label="单位" prop="unit">
          <el-input v-model="formModel.unit" placeholder="如 盒/支/瓶" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-input v-model="formModel.category" placeholder="可选" />
        </el-form-item>
        <el-form-item label="安全库存" prop="safety_stock">
          <el-input-number v-model="formModel.safety_stock" :min="0" style="width: 220px" />
        </el-form-item>
        <el-form-item label="位置" prop="location">
          <el-input v-model="formModel.location" placeholder="可选" />
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

.pane-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
}

.pagination {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.form {
  max-width: 720px;
}

.mb-12 {
  margin-bottom: 12px;
}
</style>
