<script lang="ts" setup>
import { message } from 'ant-design-vue';
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

import { useTemplateStore } from '#/store/template';

import TemplateView1 from './templateViews-1/index.vue';
import TemplateView2 from './templateViews-2/index.vue';
import TemplateView3 from './templateViews-3/index.vue';

defineOptions({ name: 'TemplateView' });

const route = useRoute();
const templateStore = useTemplateStore();

const loading = ref(false);
const template = ref<null | any>(null);

const routeDomain = computed(() =>
  decodeURIComponent(String(route.params.domain || '')),
);

const accessDomain = computed(() => {
  const normalizedRouteDomain = routeDomain.value.trim().toLowerCase();
  if (normalizedRouteDomain && normalizedRouteDomain !== '__host__') {
    return normalizedRouteDomain;
  }
  return window.location.hostname.trim().toLowerCase();
});

const templateComponent = computed(() => {
  if (!template.value) return null;
  
  const templateType = template.value.templateId;
  const componentMap: Record<string, any> = {
    'template-1': TemplateView1,
    'template-2': TemplateView2,
    'template-3': TemplateView3,
  };
  
  return componentMap[templateType] || TemplateView1;
});

onMounted(async () => {
  loading.value = true;
  try {
    template.value = await templateStore.fetchTemplateByDomain(accessDomain.value);
  } catch (error: any) {
    message.error(error?.message ?? '页面不存在或已下线');
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="template-view-wrapper">
    <div v-if="loading" class="error-page">
      <h1>页面加载中...</h1>
    </div>

    <component v-else-if="template && templateComponent" :is="templateComponent" :template="template" />

    <div v-else class="error-page">
      <h1>页面不存在</h1>
      <p>抱歉，您访问的域名未绑定页面，或页面已被删除。</p>
    </div>
  </div>
</template>

<style scoped>
.template-view-wrapper {
  width: 100%;
  min-height: 100vh;
  margin: 0;
  padding: 0;
}

.error-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  text-align: center;
  padding: 20px;
  background: #f5f5f5;
}

.error-page h1 {
  font-size: 32px;
  margin-bottom: 16px;
  color: #1a1a1a;
}

.error-page p {
  font-size: 16px;
  color: #666;
  margin-bottom: 24px;
}
</style>
