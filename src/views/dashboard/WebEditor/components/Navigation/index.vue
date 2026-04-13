<script setup lang="ts">
defineProps<{
  items?: string[]
  align?: 'left' | 'center' | 'right'
}>()
</script>

<template>
  <nav class="nav-module" :style="{ justifyContent: align === 'center' ? 'center' : align === 'right' ? 'flex-end' : 'flex-start' }">
    <a v-for="item in items || []" :key="item" href="#" class="nav-item">{{ item }}</a>
  </nav>
</template>

<style scoped>
.nav-module {
  display: flex;
  gap: 12px;
  padding: 8px;
}

.nav-item {
  text-decoration: none;
  color: #1677ff;
  font-size: 14px;
}
</style>
