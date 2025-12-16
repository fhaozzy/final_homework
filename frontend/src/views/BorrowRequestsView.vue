<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { listBorrowRequests, type BorrowRequest } from '../api/borrowing'
import { getBorrowRequestStatusLabel, getBorrowRequestStatusTagType } from '../constants/borrowing'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const loading = ref(false)
const requests = ref<BorrowRequest[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

const showApplicantColumn = computed(() => auth.hasAnyRole(['TEACHER', 'ADMIN']))

async function fetchList() {
  loading.value = true
  try {
    const data = await listBorrowRequests({ page: page.value })
    requests.value = data.results
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

function goDetail(row: BorrowRequest) {
  router.push(`/borrow/${row.id}`)
}

function goCreate() {
  router.push('/borrow/new')
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
          <div class="title">借用单列表</div>
          <div class="actions">
            <el-button type="primary" @click="goCreate">新建借用单</el-button>
          </div>
        </div>
      </template>

      <el-table v-loading="loading" :data="requests" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="90" />
        <el-table-column v-if="showApplicantColumn" prop="applicant_username" label="申请人" width="140" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getBorrowRequestStatusTagType(row.status)">{{ getBorrowRequestStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="purpose" label="用途" min-width="200" />
        <el-table-column prop="expected_return_date" label="预计归还" width="140" />
        <el-table-column label="设备数" width="100" align="center">
          <template #default="{ row }">
            {{ row.items?.length || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="140" align="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="goDetail(row)">详情</el-button>
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
