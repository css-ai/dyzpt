<script lang="ts" setup>
import { ref } from 'vue';
import { useTemplateStore } from '#/store/template';
import TemplatePreview from '../../templates/TemplatePreview.vue';

const templateStore = useTemplateStore();
const templates = templateStore.getAvailableTemplates();

const selectedTemplate = ref<string | null>(null);
const showPreview = ref(false);
const showGenerateModal = ref(false);
const siteName = ref('');
const siteDescription = ref('');
const sitePath = ref('');
const isGenerating = ref(false);

const currentTemplate = () => {
  if (!selectedTemplate.value) return null;
  return templateStore.getTemplate(selectedTemplate.value);
};

const handleSelectTemplate = (templateId: string) => {
  selectedTemplate.value = templateId;
};

const handlePreview = () => {
  if (selectedTemplate.value) {
    showPreview.value = true;
  }
};

const handleGenerateClick = () => {
  if (selectedTemplate.value) {
    showGenerateModal.value = true;
  }
};

const handleGenerate = async () => {
  if (!selectedTemplate.value || !siteName.value.trim()) {
    alert('请输入网站名称');
    return;
  }

  if (!sitePath.value.trim()) {
    alert('请输入网站路径');
    return;
  }

  // 验证路径格式
  if (!/^\/[a-zA-Z0-9_-]*$/.test(sitePath.value)) {
    alert('网站路径必须以 / 开头，只能包含字母、数字、下划线和连字符');
    return;
  }

  isGenerating.value = true;
  try {
    // 模拟生成延迟
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const result = templateStore.generateTemplate(
      selectedTemplate.value,
      siteName.value,
      siteDescription.value,
      sitePath.value,
    );

    if (result) {
      alert(`模板已生成！网站名称: ${siteName.value}\n访问路径: ${sitePath.value}`);
      siteName.value = '';
      siteDescription.value = '';
      sitePath.value = '';
      showGenerateModal.value = false;
      selectedTemplate.value = null;
    }
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
  sitePath.value = '';
};
</script>

<template>
  <div class="analytics-container">
    <div class="page-header">
      <h1>企业门户网站模板库</h1>
      <p>选择一个模板，预览效果，然后生成您的企业网站</p>
    </div>

    <!-- 模板列表 -->
    <div class="templates-grid">
      <div
        v-for="template in templates"
        :key="template.id"
        class="template-card"
        :class="{ active: selectedTemplate === template.id }"
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

    <!-- 操作按钮 -->
    <div v-if="selectedTemplate" class="action-buttons">
      <button class="btn btn-primary" @click="handlePreview">
        预览模板
      </button>
      <button class="btn btn-success" @click="handleGenerateClick">
        生成模板
      </button>
    </div>

    <!-- 预览模态框 -->
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

    <!-- 生成模态框 -->
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
            <label>网站路径 *</label>
            <input
              v-model="sitePath"
              type="text"
              placeholder="例如: /my-site 或 /company"
              class="form-input"
            />
            <small class="form-hint">必须以 / 开头，只能包含字母、数字、下划线和连字符</small>
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
