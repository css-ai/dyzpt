<script lang="ts" setup>
// message：全局轻提示，用于操作成功/失败反馈
import { message } from 'ant-design-vue';
// computed：计算属性；onMounted：挂载钩子；ref：响应式变量
import { computed, onMounted, ref } from 'vue';

// useUserStore：获取当前登录用户信息（用于读取配额）
import { useUserStore } from '@vben/stores';

// useTemplateStore：模板/站点页面的核心 store（增删查、配额校验等）
import { useTemplateStore } from '#/store/template';

// TemplatePreview：模板预览组件，在弹窗中渲染所选模板效果
import TemplatePreview from '../../templates/TemplatePreview.vue';

const templateStore = useTemplateStore();
const templates = templateStore.getAvailableTemplates();

const selectedTemplate = ref<string | null>(null);
const showPreview = ref(false);
const showGenerateModal = ref(false);
const siteName = ref('');
const siteDescription = ref('');
const domain = ref('');
const isGenerating = ref(false);

const currentTemplate = () => {
  if (!selectedTemplate.value) return null;
  return templateStore.getTemplate(selectedTemplate.value);
};

const canCreate = computed(() => templateStore.canCreateMore());

const maxPages = computed(() => {
  const info = (useUserStore().userInfo as any);
  const quota = info?.pageQuota;
  if (!quota) return 1;
  return quota.maxPages === -1 ? '无限' : quota.maxPages;
});

const domainReg = /^(?=.{3,255}$)([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$/;

onMounted(async () => {
  try {
    await templateStore.loadMyGeneratedTemplates();
  } catch (error: any) {
    message.error(error?.message ?? '加载页面列表失败');
  }
});

const handleSelectTemplate = (templateId: string) => {
  if (!canCreate.value) {
    message.warning(`当前账号最多创建 ${maxPages.value} 个页面，请先删除旧页面或联系管理员`);
    return;
  }
  selectedTemplate.value = templateId;
};

const handlePreview = () => {
  if (selectedTemplate.value) {
    showPreview.value = true;
  }
};

const handleGenerateClick = () => {
  if (!canCreate.value) {
    message.warning(`当前账号最多创建 ${maxPages.value} 个页面，请先删除旧页面或联系管理员`);
    return;
  }
  if (selectedTemplate.value) {
    showGenerateModal.value = true;
  }
};

const handleGenerate = async () => {
  if (!selectedTemplate.value || !siteName.value.trim()) {
    message.error('请输入网站名称');
    return;
  }

  const normalizedDomain = domain.value.trim().toLowerCase();
  if (!normalizedDomain) {
    message.error('请输入域名');
    return;
  }

  if (!domainReg.test(normalizedDomain)) {
    message.error('请输入正确域名，例如：demo.example.com');
    return;
  }

  isGenerating.value = true;
  try {
    const result = await templateStore.generateTemplate(
      selectedTemplate.value,
      siteName.value.trim(),
      siteDescription.value.trim(),
      normalizedDomain,
    );

    message.success(`模板已生成，绑定域名：${result.domain}`);
      siteName.value = '';
      siteDescription.value = '';
    domain.value = '';
      showGenerateModal.value = false;
      selectedTemplate.value = null;
  } catch (error: any) {
    message.error(error?.message ?? '生成失败，请稍后重试');
  } finally {
    isGenerating.value = false;
  }
};

const handleClosePreview = () => {
  showPreview.value = false;
};

const handleCloseModal = () => {
  showGenerateModal.value = false;
  siteName.value = '';
  siteDescription.value = '';
  domain.value = '';
};
</script>

<template>
  <div class="analytics-container">
    <div class="page-header">
      <h1>企业门户网站模板库</h1>
      <p>选择模板后生成网站，并绑定您申请的域名</p>
      <p v-if="!canCreate" class="limit-tip">当前账号最多创建 {{ maxPages }} 个页面</p>
    </div>

    <div class="templates-grid">
      <div
        v-for="template in templates"
        :key="template.id"
        class="template-card"
        :class="{ active: selectedTemplate === template.id, disabled: !canCreate }"
        @click="handleSelectTemplate(template.id)"
      >
        <div class="template-thumbnail">
          <img :src="template.thumbnail" :alt="template.name" />
        </div>
        <div class="template-info">
          <h3>{{ template.name }}</h3>
          <p>{{ template.description }}</p>
          <div class="template-meta">
            <span class="category-badge">{{ template.category }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="selectedTemplate" class="action-buttons">
      <button class="btn btn-primary" @click="handlePreview">预览模板</button>
      <button class="btn btn-success" @click="handleGenerateClick">生成模板</button>
    </div>

    <div v-if="showPreview" class="modal-overlay" @click="handleClosePreview">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>模板预览</h2>
          <button class="close-btn" @click="handleClosePreview">×</button>
        </div>
        <div class="modal-body">
          <TemplatePreview v-if="currentTemplate()" :template="currentTemplate()!" />
        </div>
      </div>
    </div>

    <div v-if="showGenerateModal" class="modal-overlay" @click="handleCloseModal">
      <div class="modal-content modal-form" @click.stop>
        <div class="modal-header">
          <h2>生成新模板</h2>
          <button class="close-btn" @click="handleCloseModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>选择的模板</label>
            <input
              type="text"
              :value="currentTemplate()?.name"
              disabled
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label>网站名称 *</label>
            <input
              v-model="siteName"
              type="text"
              placeholder="请输入您的企业网站名称"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label>网站描述</label>
            <textarea
              v-model="siteDescription"
              placeholder="请输入网站描述（可选）"
              class="form-textarea"
              rows="4"
            ></textarea>
          </div>
          <div class="form-group">
            <label>绑定域名 *</label>
            <input
              v-model="domain"
              type="text"
              placeholder="例如: demo.example.com"
              class="form-input"
            />
            <small class="form-hint">请输入已备案并解析到本系统的域名</small>
          </div>
          <div class="form-actions">
            <button
              class="btn btn-secondary"
              @click="handleCloseModal"
              :disabled="isGenerating"
            >
              取消
            </button>
            <button
              class="btn btn-success"
              @click="handleGenerate"
              :disabled="isGenerating"
            >
              {{ isGenerating ? '生成中...' : '确认生成' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.analytics-container {
  padding: 24px;
  background: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 32px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  color: #1a1a1a;
}

.page-header p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.limit-tip {
  margin-top: 8px !important;
  color: #d4380d !important;
  font-weight: 500;
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.template-card {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.template-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.template-card.disabled {
  opacity: 0.6;
}

.template-card.active {
  border-color: #0066cc;
  box-shadow: 0 4px 16px rgba(0, 102, 204, 0.3);
}

.template-thumbnail {
  width: 100%;
  height: 180px;
  background: #f0f0f0;
  overflow: hidden;
}

.template-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.template-info {
  padding: 16px;
}

.template-info h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #1a1a1a;
}

.template-info p {
  margin: 0 0 12px 0;
  font-size: 13px;
  color: #666;
  line-height: 1.5;
}

.template-meta {
  display: flex;
  gap: 8px;
}

.category-badge {
  display: inline-block;
  padding: 4px 12px;
  background: #e6f2ff;
  color: #0066cc;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 32px;
}

.btn {
  padding: 10px 24px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #0066cc;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0052a3;
}

.btn-success {
  background: #52c41a;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #389e0d;
}

.btn-secondary {
  background: #d9d9d9;
  color: #1a1a1a;
}

.btn-secondary:hover:not(:disabled) {
  background: #bfbfbf;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 800px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
}

.modal-form {
  max-width: 500px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h2 {
  margin: 0;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #1a1a1a;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #1a1a1a;
  font-size: 14px;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.3s;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #0066cc;
  box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.1);
}

.form-input:disabled {
  background: #f5f5f5;
  color: #999;
}

.form-textarea {
  resize: vertical;
}

.form-hint {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: #999;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
}
</style>
