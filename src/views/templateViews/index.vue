<script lang="ts" setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useTemplateStore } from '#/store/template';
import TemplateView1 from './templateViews-1/index.vue';
import TemplateView2 from './templateViews-2/index.vue';
import TemplateView3 from './templateViews-3/index.vue';

defineOptions({ name: 'TemplateView' });

const route = useRoute();
const templateStore = useTemplateStore();

// 从路由参数获取网站路径
const sitePath = computed(() => `/${route.params.path as string}`);
// 通过网站路径查找模板
const template = computed(() => templateStore.getGeneratedTemplateByPath(sitePath.value));

// 根据模板类型选择对应的视图组件
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
</script>

<template>
  <div class="template-view-wrapper">
    <component v-if="template && templateComponent" :is="templateComponent" :template="template" />
    <div v-else class="error-page">
      <h1>模板不存在</h1>
      <p>抱歉，您访问的模板不存在或已被删除。</p>
      <a href="/analytics">返回模板库</a>
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

.error-page a {
  padding: 10px 24px;
  background: #0066cc;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  transition: all 0.3s;
}

.error-page a:hover {
  background: #0052a3;
}
</style>

