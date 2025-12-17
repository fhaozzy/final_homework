<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'

import AppPagination from '../../components/AppPagination.vue'
import {
  activateUser,
  createUser,
  createUserRole,
  deactivateUser,
  deleteUser,
  deleteUserRole,
  fetchAllRoles,
  fetchAllUserRoles,
  listUsers,
  updateUser,
  type Role,
  type User,
  type UserRole,
} from '../../api/admin'
import { notifyApiError } from '../../utils/apiError'
import { requiredRule, emailRule } from '../../utils/rules'

const loading = ref(false)
const users = ref<User[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

async function fetchUsers() {
  loading.value = true
  try {
    const data = await listUsers({ page: page.value })
    users.value = data.results
    total.value = data.count
    if (page.value === 1 && data.results.length) {
      pageSize.value = data.results.length
    }
  } catch (err) {
    notifyApiError(err, '加载用户失败')
  } finally {
    loading.value = false
  }
}

// Roles & UserRoles
const rolesLoading = ref(false)
const roles = ref<Role[]>([])
const userRolesLoading = ref(false)
const userRolesByUserId = ref<Record<number, UserRole[]>>({})

const roleOptions = computed(() =>
  roles.value.map((r) => ({
    label: `${r.name}(${r.code})`,
    value: r.id,
  })),
)

function getUserRoles(userId: number): UserRole[] {
  return userRolesByUserId.value[userId] ?? []
}

async function refreshRoles() {
  rolesLoading.value = true
  try {
    roles.value = await fetchAllRoles()
  } catch (err) {
    notifyApiError(err, '加载角色失败')
  } finally {
    rolesLoading.value = false
  }
}

async function refreshUserRoles() {
  userRolesLoading.value = true
  try {
    const all = await fetchAllUserRoles()
    const grouped: Record<number, UserRole[]> = {}
    for (const ur of all) {
      const key = ur.user
      const bucket = grouped[key] ?? (grouped[key] = [])
      bucket.push(ur)
    }
    userRolesByUserId.value = grouped
  } catch (err) {
    notifyApiError(err, '加载用户角色失败')
  } finally {
    userRolesLoading.value = false
  }
}

// User create/edit
const userDialogVisible = ref(false)
const savingUser = ref(false)
const editingUser = ref<User | null>(null)
const userFormRef = ref<FormInstance>()
const userForm = reactive({
  username: '',
  password: '',
  email: '',
  real_name: '',
  phone: '',
  is_active: true,
})

function resetUserForm() {
  userForm.username = ''
  userForm.password = ''
  userForm.email = ''
  userForm.real_name = ''
  userForm.phone = ''
  userForm.is_active = true
}

function openCreateUser() {
  editingUser.value = null
  resetUserForm()
  userDialogVisible.value = true
}

function openEditUser(row: User) {
  editingUser.value = row
  userForm.username = row.username
  userForm.password = ''
  userForm.email = row.email || ''
  userForm.real_name = row.real_name || ''
  userForm.phone = row.phone || ''
  userForm.is_active = Boolean(row.is_active)
  userDialogVisible.value = true
}

function validatePassword(_: any, value: string, callback: (err?: Error) => void) {
  const v = value?.trim() ?? ''
  if (!editingUser.value && !v) {
    callback(new Error('请输入密码'))
    return
  }
  if (v && v.length < 6) {
    callback(new Error('密码至少 6 位'))
    return
  }
  callback()
}

const userRules: FormRules = {
  username: [requiredRule('请输入用户名', 'blur')],
  password: [{ validator: validatePassword, trigger: 'blur' }],
  email: [emailRule('邮箱格式不正确', 'blur')],
}

async function onSaveUser() {
  const isValid = await userFormRef.value?.validate().catch(() => false)
  if (!isValid) return

  savingUser.value = true
  try {
    const payloadBase = {
      username: userForm.username.trim(),
      email: userForm.email.trim(),
      real_name: userForm.real_name.trim(),
      phone: userForm.phone.trim(),
      is_active: userForm.is_active,
    }

    if (!editingUser.value) {
      await createUser({
        ...payloadBase,
        password: userForm.password.trim(),
      })
      ElMessage.success('用户已创建')
      page.value = 1
    } else {
      const password = userForm.password.trim()
      await updateUser(editingUser.value.id, {
        ...payloadBase,
        ...(password ? { password } : {}),
      })
      ElMessage.success('用户已更新')
    }

    userDialogVisible.value = false
    await fetchUsers()
    await refreshUserRoles()
  } catch (err) {
    notifyApiError(err, '保存失败')
  } finally {
    savingUser.value = false
  }
}

async function onDeleteUser(row: User) {
  try {
    await ElMessageBox.confirm(`确认删除用户「${row.username}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }

  try {
    await deleteUser(row.id)
    ElMessage.success('已删除')
    if (users.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    await fetchUsers()
    await refreshUserRoles()
  } catch (err) {
    notifyApiError(err, '删除失败')
  }
}

async function onToggleActive(row: User) {
  const next = !row.is_active
  try {
    await ElMessageBox.confirm(
      next ? `确认启用用户「${row.username}」？` : `确认停用用户「${row.username}」？`,
      '提示',
      { type: 'warning' },
    )
  } catch {
    return
  }

  try {
    if (next) {
      await activateUser(row.id)
      ElMessage.success('已启用')
    } else {
      await deactivateUser(row.id)
      ElMessage.success('已停用')
    }
    await fetchUsers()
  } catch (err) {
    notifyApiError(err, '操作失败')
  }
}

// Role assignment dialog
const assignDialogVisible = ref(false)
const assigning = ref(false)
const assignUser = ref<User | null>(null)
const selectedRoleIds = ref<number[]>([])

function openAssignRoles(row: User) {
  assignUser.value = row
  const urs = getUserRoles(row.id)
  selectedRoleIds.value = urs.map((ur) => ur.role)
  assignDialogVisible.value = true
}

async function onSaveRoles() {
  if (!assignUser.value) return
  const userId = assignUser.value.id

  assigning.value = true
  try {
    const current = getUserRoles(userId)
    const currentRoleIds = new Set(current.map((ur) => ur.role))
    const nextRoleIds = new Set(selectedRoleIds.value)

    const tasks: Promise<any>[] = []

    for (const ur of current) {
      if (!nextRoleIds.has(ur.role)) {
        tasks.push(deleteUserRole(ur.id))
      }
    }

    for (const roleId of selectedRoleIds.value) {
      if (!currentRoleIds.has(roleId)) {
        tasks.push(createUserRole({ user: userId, role: roleId }))
      }
    }

    await Promise.all(tasks)
    ElMessage.success('角色已更新')
    assignDialogVisible.value = false
    await refreshUserRoles()
  } catch (err) {
    notifyApiError(err, '更新角色失败')
  } finally {
    assigning.value = false
  }
}

onMounted(async () => {
  await Promise.all([fetchUsers(), refreshRoles(), refreshUserRoles()])
})
</script>

<template>
  <el-space direction="vertical" fill size="large">
    <el-card>
      <template #header>
        <div class="header">
          <div class="title">用户管理</div>
          <div class="actions">
            <el-button type="primary" @click="openCreateUser">新增用户</el-button>
            <el-button :loading="rolesLoading || userRolesLoading" @click="refreshUserRoles">刷新角色绑定</el-button>
          </div>
        </div>
      </template>

      <el-table v-loading="loading" :data="users" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="90" />
        <el-table-column prop="username" label="用户名" width="160" />
        <el-table-column prop="real_name" label="姓名" width="140" />
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column prop="phone" label="手机" width="140" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="角色" min-width="220">
          <template #default="{ row }">
            <el-space wrap>
              <el-tag v-for="ur in getUserRoles(row.id)" :key="ur.id" size="small" type="info">
                {{ ur.role_code }}
              </el-tag>
              <span v-if="getUserRoles(row.id).length === 0" class="muted">-</span>
            </el-space>
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最近登录" width="180" />
        <el-table-column label="操作" width="260" align="right">
          <template #default="{ row }">
            <el-space>
              <el-button link type="primary" @click="openEditUser(row)">编辑</el-button>
              <el-button link type="warning" @click="openAssignRoles(row)">分配角色</el-button>
              <el-button link type="success" @click="onToggleActive(row)">
                {{ row.is_active ? '停用' : '启用' }}
              </el-button>
              <el-button link type="danger" @click="onDeleteUser(row)">删除</el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>

      <AppPagination v-model:page="page" :page-size="pageSize" :total="total" @change="fetchUsers" />
    </el-card>

    <el-dialog v-model="userDialogVisible" :title="editingUser ? '编辑用户' : '新增用户'" width="720px">
      <el-form ref="userFormRef" :model="userForm" :rules="userRules" label-width="90px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" placeholder="如 student1" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="userForm.password"
            type="password"
            show-password
            :placeholder="editingUser ? '留空则不修改' : '至少 6 位'"
          />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" placeholder="可选" />
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="userForm.real_name" placeholder="可选" />
        </el-form-item>
        <el-form-item label="手机" prop="phone">
          <el-input v-model="userForm.phone" placeholder="可选" />
        </el-form-item>
        <el-form-item label="启用" prop="is_active">
          <el-switch v-model="userForm.is_active" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-space>
          <el-button @click="userDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="savingUser" @click="onSaveUser">保存</el-button>
        </el-space>
      </template>
    </el-dialog>

    <el-dialog v-model="assignDialogVisible" title="分配角色" width="640px">
      <div v-if="assignUser" class="assign-header">
        用户：<b>{{ assignUser.username }}</b>
      </div>
      <el-form label-width="90px">
        <el-form-item label="角色">
          <el-select v-model="selectedRoleIds" multiple filterable placeholder="请选择" style="width: 420px">
            <el-option v-for="opt in roleOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-space>
          <el-button @click="assignDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="assigning" @click="onSaveRoles">保存</el-button>
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

.muted {
  color: var(--el-text-color-secondary);
}

.assign-header {
  margin-bottom: 10px;
  color: var(--el-text-color-secondary);
}
</style>
