<script setup lang="ts">
defineProps<{
  text?: string
  align?: 'left' | 'center' | 'right'
}>()
</script>

<template>
  <div class="text-module" :style="{ textAlign: align || 'left' }">
    {{ text || '（空文本）' }}
  </div>
</template>

<style scoped>
.text-module {
  font-size: 16px;
  line-height: 1.8;
  padding: 8px;
}
</style>
