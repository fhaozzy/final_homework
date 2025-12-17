<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    page: number
    pageSize: number
    total: number
    layout?: string
    hideOnSinglePage?: boolean
  }>(),
  {
    layout: 'total, prev, pager, next',
    hideOnSinglePage: true,
  },
)

const emit = defineEmits<{
  (e: 'update:page', value: number): void
  (e: 'change', value: number): void
}>()

function onChange(value: number) {
  emit('update:page', value)
  emit('change', value)
}
</script>

<template>
  <div class="pagination">
    <el-pagination
      :current-page="props.page"
      :page-size="props.pageSize"
      :total="props.total"
      :layout="props.layout"
      :hide-on-single-page="props.hideOnSinglePage"
      @current-change="onChange"
    />
  </div>
</template>

<style scoped>
.pagination {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>

