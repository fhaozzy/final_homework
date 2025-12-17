<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'

import AppPagination from '../../components/AppPagination.vue'
import {
  createRole,
  createUserRole,
  deleteRole,
  deleteUserRole,
  fetchAllRoles,
  fetchAllUsers,
  listRoles,
  listUserRoles,
  updateRole,
  type Role,
  type User,
  type UserRole,
} from '../../api/admin'
import { notifyApiError } from '../../utils/apiError'
import { requiredRule } from '../../utils/rules'

const activeTab = ref<'roles' | 'userRoles'>('roles')

// Roles tab
const rolesLoading = ref(false)
const roles = ref<Role[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

async function fetchRoles() {
  rolesLoading.value = true
  try {
    const data = await listRoles({ page: page.value })
    roles.value = data.results
    total.value = data.count
    if (page.value === 1 && data.results.length) {
      pageSize.value = data.results.length
    }
  } catch (err) {
    notifyApiError(err, '加载角色失败')
  } finally {
    rolesLoading.value = false
  }
}

const roleDialogVisible = ref(false)
const savingRole = ref(false)
const editingRole = ref<Role | null>(null)
const roleFormRef = ref<FormInstance>()
const roleForm = reactive({
  code: '',
  name: '',
})

const roleRules: FormRules = {
  code: [requiredRule('请输入角色编码', 'blur')],
  name: [requiredRule('请输入角色名称', 'blur')],
}

function openCreateRole() {
  editingRole.value = null
  roleForm.code = ''
  roleForm.name = ''
  roleDialogVisible.value = true
}

function openEditRole(row: Role) {
  editingRole.value = row
  roleForm.code = row.code
  roleForm.name = row.name
  roleDialogVisible.value = true
}

async function onSaveRole() {
  const isValid = await roleFormRef.value?.validate().catch(() => false)
  if (!isValid) return

  savingRole.value = true
  try {
    const payload = { code: roleForm.code.trim(), name: roleForm.name.trim() }
    if (!editingRole.value) {
      await createRole(payload)
      ElMessage.success('角色已创建')
      page.value = 1
    } else {
      await updateRole(editingRole.value.id, payload)
      ElMessage.success('角色已更新')
    }
    roleDialogVisible.value = false
    await fetchRoles()
    await refreshAllOptions()
  } catch (err) {
    notifyApiError(err, '保存失败')
  } finally {
    savingRole.value = false
  }
}

async function onDeleteRole(row: Role) {
  try {
    await ElMessageBox.confirm(`确认删除角色「${row.code}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }

  try {
    await deleteRole(row.id)
    ElMessage.success('已删除')
    if (roles.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    await fetchRoles()
    await refreshAllOptions()
  } catch (err) {
    notifyApiError(err, '删除失败')
  }
}

// UserRole tab
const usersOptionsLoading = ref(false)
const allUsers = ref<User[]>([])
const allRoles = ref<Role[]>([])

const userOptions = computed(() =>
  allUsers.value.map((u) => ({
    label: u.username,
    value: u.id,
  })),
)
const allRoleOptions = computed(() =>
  allRoles.value.map((r) => ({
    label: `${r.name}(${r.code})`,
    value: r.id,
  })),
)

async function refreshAllOptions() {
  usersOptionsLoading.value = true
  try {
    const [users, roles] = await Promise.all([fetchAllUsers(), fetchAllRoles()])
    allUsers.value = users
    allRoles.value = roles
  } catch (err) {
    notifyApiError(err, '加载用户/角色选项失败')
  } finally {
    usersOptionsLoading.value = false
  }
}

const assignRef = ref<FormInstance>()
const assignForm = reactive({
  user: undefined as number | undefined,
  role: undefined as number | undefined,
})
const assignRules: FormRules = {
  user: [requiredRule('请选择用户', 'change')],
  role: [requiredRule('请选择角色', 'change')],
}
const assigning = ref(false)

async function onAssign() {
  const isValid = await assignRef.value?.validate().catch(() => false)
  if (!isValid) return

  assigning.value = true
  try {
    await createUserRole({ user: assignForm.user as number, role: assignForm.role as number })
    ElMessage.success('已绑定')
    await fetchUserRoles()
  } catch (err) {
    notifyApiError(err, '绑定失败')
  } finally {
    assigning.value = false
  }
}

const userRolesLoading = ref(false)
const userRoles = ref<UserRole[]>([])
const userRoleTotal = ref(0)
const userRolePage = ref(1)
const userRolePageSize = ref(10)

async function fetchUserRoles() {
  userRolesLoading.value = true
  try {
    const data = await listUserRoles({ page: userRolePage.value })
    userRoles.value = data.results
    userRoleTotal.value = data.count
    if (userRolePage.value === 1 && data.results.length) {
      userRolePageSize.value = data.results.length
    }
  } catch (err) {
    notifyApiError(err, '加载用户角色失败')
  } finally {
    userRolesLoading.value = false
  }
}

async function onRemoveUserRole(row: UserRole) {
  try {
    await ElMessageBox.confirm(
      `确认移除用户「${row.user_username}」的角色「${row.role_code}」？`,
      '提示',
      { type: 'warning' },
    )
  } catch {
    return
  }

  try {
    await deleteUserRole(row.id)
    ElMessage.success('已移除')
    if (userRoles.value.length === 1 && userRolePage.value > 1) {
      userRolePage.value -= 1
    }
    await fetchUserRoles()
  } catch (err) {
    notifyApiError(err, '移除失败')
  }
}

onMounted(async () => {
  await Promise.all([fetchRoles(), refreshAllOptions(), fetchUserRoles()])
})
</script>

<template>
  <el-space direction="vertical" fill size="large">
    <el-card>
      <template #header>
        <div class="header">
          <div class="title">角色与权限</div>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="角色管理" name="roles">
          <div class="pane-header">
            <el-button type="primary" @click="openCreateRole">新增角色</el-button>
          </div>

          <el-table v-loading="rolesLoading" :data="roles" stripe style="width: 100%">
            <el-table-column prop="id" label="ID" width="90" />
            <el-table-column prop="code" label="编码" width="180" />
            <el-table-column prop="name" label="名称" min-width="240" />
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column label="操作" width="180" align="right">
              <template #default="{ row }">
                <el-space>
                  <el-button link type="primary" @click="openEditRole(row)">编辑</el-button>
                  <el-button link type="danger" @click="onDeleteRole(row)">删除</el-button>
                </el-space>
              </template>
            </el-table-column>
          </el-table>

          <AppPagination v-model:page="page" :page-size="pageSize" :total="total" @change="fetchRoles" />
        </el-tab-pane>

        <el-tab-pane label="用户角色分配" name="userRoles">
          <el-form ref="assignRef" :model="assignForm" :rules="assignRules" :inline="true" class="assign">
            <el-form-item label="用户" prop="user">
              <el-select
                v-model="assignForm.user"
                filterable
                :loading="usersOptionsLoading"
                placeholder="请选择"
                style="width: 220px"
              >
                <el-option v-for="opt in userOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="角色" prop="role">
              <el-select
                v-model="assignForm.role"
                filterable
                :loading="usersOptionsLoading"
                placeholder="请选择"
                style="width: 240px"
              >
                <el-option v-for="opt in allRoleOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-space>
                <el-button type="primary" :loading="assigning" @click="onAssign">绑定</el-button>
                <el-button :loading="usersOptionsLoading" @click="refreshAllOptions">刷新选项</el-button>
                <el-button @click="fetchUserRoles">刷新列表</el-button>
              </el-space>
            </el-form-item>
          </el-form>

          <el-table v-loading="userRolesLoading" :data="userRoles" stripe style="width: 100%">
            <el-table-column prop="id" label="ID" width="90" />
            <el-table-column prop="user_username" label="用户" width="180" />
            <el-table-column prop="role_code" label="角色编码" width="160" />
            <el-table-column prop="role_name" label="角色名称" min-width="220" />
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column label="操作" width="120" align="right">
              <template #default="{ row }">
                <el-button link type="danger" @click="onRemoveUserRole(row)">移除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <AppPagination
            v-model:page="userRolePage"
            :page-size="userRolePageSize"
            :total="userRoleTotal"
            @change="fetchUserRoles"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="roleDialogVisible" :title="editingRole ? '编辑角色' : '新增角色'" width="560px">
      <el-form ref="roleFormRef" :model="roleForm" :rules="roleRules" label-width="90px">
        <el-form-item label="编码" prop="code">
          <el-input v-model="roleForm.code" placeholder="如 STUDENT/TEACHER/MAINTAINER/ADMIN" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="roleForm.name" placeholder="如 学生/老师/维修员/管理员" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-space>
          <el-button @click="roleDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="savingRole" @click="onSaveRole">保存</el-button>
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

.pane-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
}

.assign {
  margin-bottom: 10px;
}
</style>
