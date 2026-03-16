<script lang="ts" setup>
import { ref, computed } from 'vue';
import { useTemplateStore, type GeneratedTemplate, type NavItem } from '#/store/template';

const templateStore = useTemplateStore();
const generatedTemplates = computed(() => templateStore.getGeneratedTemplates());

const selectedTemplate = ref<string | null>(null);
const showEditModal = ref(false);
const showNavEditor = ref(false);
const editingTemplate = ref<GeneratedTemplate | null>(null);
const editingNavItem = ref<NavItem | null>(null);
const editingNavIndex = ref<number | null>(null);

const currentTemplate = computed(() => {
  if (!selectedTemplate.value) return null;
  return templateStore.getGeneratedTemplate(selectedTemplate.value);
});

const handleSelectTemplate = (templateId: string) => {
  selectedTemplate.value = templateId;
};

const handleEditClick = () => {
  if (currentTemplate.value) {
    editingTemplate.value = JSON.parse(JSON.stringify(currentTemplate.value));
    showEditModal.value = true;
  }
};

const handleSaveEdit = () => {
  if (editingTemplate.value) {
    templateStore.updateGeneratedTemplate(editingTemplate.value.id, {
      siteName: editingTemplate.value.siteName,
      siteDescription: editingTemplate.value.siteDescription,
      navItems: editingTemplate.value.navItems,
      colors: editingTemplate.value.colors,
      fonts: editingTemplate.value.fonts,
    });
    showEditModal.value = false;
    editingTemplate.value = null;
    alert('模板已更新');
  }
};

const handleCloseModal = () => {
  showEditModal.value = false;
  editingTemplate.value = null;
};

const handleDeleteTemplate = (id: string) => {
  if (confirm('确定要删除这个模板吗？')) {
    templateStore.deleteGeneratedTemplate(id);
    if (selectedTemplate.value === id) {
      selectedTemplate.value = null;
    }
    alert('模板已删除');
  }
};

const handleEditNav = (index: number) => {
  if (editingTemplate.value) {
    editingNavIndex.value = index;
    editingNavItem.value = JSON.parse(JSON.stringify(editingTemplate.value.navItems[index]));
    showNavEditor.value = true;
  }
};

const handleSaveNav = () => {
  if (editingTemplate.value && editingNavItem.value !== null && editingNavIndex.value !== null) {
    editingTemplate.value.navItems[editingNavIndex.value] = editingNavItem.value;
    showNavEditor.value = false;
    editingNavItem.value = null;
    editingNavIndex.value = null;
  }
};

const handleCloseNavEditor = () => {
  showNavEditor.value = false;
  editingNavItem.value = null;
  editingNavIndex.value = null;
};

const handleAddNavItem = () => {
  if (editingTemplate.value) {
    editingTemplate.value.navItems.push({
      name: '新菜单项',
      route: '/new-item',
      children: [],
    });
  }
};

const handleRemoveNavItem = (index: number) => {
  if (editingTemplate.value) {
    editingTemplate.value.navItems.splice(index, 1);
  }
};
</script>

<template>
  <div class="workspace-container">
    <div class="page-header">
      <h1>模板管理工作区</h1>
      <p>管理和编辑您生成的企业网站模板</p>
    </div>

    <div v-if="generatedTemplates.length === 0" class="empty-state">
      <div class="empty-icon">📋</div>
      <h2>还没有生成任何模板</h2>
      <p>请先在模板库中选择一个模板并生成</p>
    </div>

    <div v-else class="workspace-content">
      <!-- 模板列表 -->
      <div class="templates-list">
        <h2>已生成的模板</h2>
        <div class="list-items">
          <div
            v-for="template in generatedTemplates"
            :key="template.id"
            class="list-item"
            :class="{ active: selectedTemplate === template.id }"
            @click="handleSelectTemplate(template.id)"
          >
            <div class="item-header">
              <h3>{{ template.siteName }}</h3>
              <span class="item-date">{{ new Date(template.createdAt).toLocaleDateString('zh-CN') }}</span>
            </div>
            <p class="item-desc">{{ template.siteDescription || '暂无描述' }}</p>
            <div class="item-template">基于: {{ template.templateName }}</div>
          </div>
        </div>
      </div>

      <!-- 编辑面板 -->
      <div v-if="currentTemplate" class="edit-panel">
        <div class="panel-header">
          <h2>{{ currentTemplate.siteName }}</h2>
          <div class="panel-actions">
            <button class="btn btn-primary" @click="handleEditClick">
              编辑模板
            </button>
            <button class="btn btn-danger" @click="handleDeleteTemplate(currentTemplate.id)">
              删除
            </button>
          </div>
        </div>

        <div class="panel-content">
          <div class="info-section">
            <h3>基本信息</h3>
            <div class="info-grid">
              <div class="info-item">
                <label>网站名称</label>
                <p>{{ currentTemplate.siteName }}</p>
              </div>
              <div class="info-item">
                <label>网站描述</label>
                <p>{{ currentTemplate.siteDescription || '暂无描述' }}</p>
              </div>
              <div class="info-item">
                <label>基础模板</label>
                <p>{{ currentTemplate.templateName }}</p>
              </div>
              <div class="info-item">
                <label>创建时间</label>
                <p>{{ new Date(currentTemplate.createdAt).toLocaleString('zh-CN') }}</p>
              </div>
              <div class="info-item">
                <label>网站路径</label>
                <p class="site-path">{{ currentTemplate.sitePath }}</p>
              </div>
              <div class="info-item">
                <label>访问链接</label>
                <a :href="`/site${currentTemplate.sitePath}`" target="_blank" class="site-link">
                  访问网站 →
                </a>
              </div>
            </div>
          </div>

          <div class="style-section">
            <h3>样式配置</h3>
            <div class="colors-grid">
              <div class="color-item">
                <label>主色</label>
                <div class="color-display">
                  <div class="color-box" :style="{ backgroundColor: currentTemplate.colors.primary }"></div>
                  <span>{{ currentTemplate.colors.primary }}</span>
                </div>
              </div>
              <div class="color-item">
                <label>辅色</label>
                <div class="color-display">
                  <div class="color-box" :style="{ backgroundColor: currentTemplate.colors.secondary }"></div>
                  <span>{{ currentTemplate.colors.secondary }}</span>
                </div>
              </div>
              <div class="color-item">
                <label>背景色</label>
                <div class="color-display">
                  <div class="color-box" :style="{ backgroundColor: currentTemplate.colors.background }"></div>
                  <span>{{ currentTemplate.colors.background }}</span>
                </div>
              </div>
              <div class="color-item">
                <label>文字色</label>
                <div class="color-display">
                  <div class="color-box" :style="{ backgroundColor: currentTemplate.colors.text }"></div>
                  <span>{{ currentTemplate.colors.text }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="nav-section">
            <h3>导航菜单</h3>
            <div class="nav-list">
              <div v-for="(item, index) in currentTemplate.navItems" :key="index" class="nav-item-display">
                <div class="nav-item-info">
                  <span class="nav-name">{{ item.name }}</span>
                  <span class="nav-route">{{ item.route }}</span>
                  <span v-if="item.children?.length" class="nav-children">
                    {{ item.children.length }} 个子菜单
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑模态框 -->
    <div v-if="showEditModal && editingTemplate" class="modal-overlay" @click="handleCloseModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>编辑模板</h2>
          <button class="close-btn" @click="handleCloseModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>网站名称</label>
            <input v-model="editingTemplate.siteName" type="text" class="form-input" />
          </div>

          <div class="form-group">
            <label>网站描述</label>
            <textarea v-model="editingTemplate.siteDescription" class="form-textarea" rows="3"></textarea>
          </div>

          <div class="form-section">
            <h3>颜色配置</h3>
            <div class="color-inputs">
              <div class="color-input-group">
                <label>主色</label>
                <input v-model="editingTemplate.colors.primary" type="color" class="color-picker" />
              </div>
              <div class="color-input-group">
                <label>辅色</label>
                <input v-model="editingTemplate.colors.secondary" type="color" class="color-picker" />
              </div>
              <div class="color-input-group">
                <label>背景色</label>
                <input v-model="editingTemplate.colors.background" type="color" class="color-picker" />
              </div>
              <div class="color-input-group">
                <label>文字色</label>
                <input v-model="editingTemplate.colors.text" type="color" class="color-picker" />
              </div>
            </div>
          </div>

          <div class="form-section">
            <div class="section-header">
              <h3>导航菜单</h3>
              <button class="btn btn-small" @click="handleAddNavItem">+ 添加菜单项</button>
            </div>
            <div class="nav-edit-list">
              <div v-for="(item, index) in editingTemplate.navItems" :key="index" class="nav-edit-item">
                <div class="nav-edit-info">
                  <input v-model="item.name" type="text" placeholder="菜单名称" class="form-input" />
                  <input v-model="item.route" type="text" placeholder="路由路径" class="form-input" />
                </div>
                <div class="nav-edit-actions">
                  <button class="btn btn-small" @click="handleEditNav(index)">编辑</button>
                  <button class="btn btn-small btn-danger" @click="handleRemoveNavItem(index)">删除</button>
                </div>
              </div>
            </div>
          </div>

          <div class="form-actions">
            <button class="btn btn-secondary" @click="handleCloseModal">取消</button>
            <button class="btn btn-success" @click="handleSaveEdit">保存更改</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 导航编辑器 -->
    <div v-if="showNavEditor && editingNavItem" class="modal-overlay" @click="handleCloseNavEditor">
      <div class="modal-content modal-small" @click.stop>
        <div class="modal-header">
          <h2>编辑菜单项</h2>
          <button class="close-btn" @click="handleCloseNavEditor">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>菜单名称</label>
            <input v-model="editingNavItem.name" type="text" class="form-input" />
          </div>
          <div class="form-group">
            <label>路由路径</label>
            <input v-model="editingNavItem.route" type="text" class="form-input" />
          </div>
          <div class="form-group">
            <label>图标</label>
            <input v-model="editingNavItem.icon" type="text" placeholder="例如: lucide:home" class="form-input" />
          </div>
          <div class="form-actions">
            <button class="btn btn-secondary" @click="handleCloseNavEditor">取消</button>
            <button class="btn btn-success" @click="handleSaveNav">保存</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.workspace-container {
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

.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 8px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state h2 {
  margin: 0 0 8px 0;
  color: #1a1a1a;
}

.empty-state p {
  margin: 0;
  color: #666;
}

.workspace-content {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 24px;
}

.templates-list {
  background: white;
  border-radius: 8px;
  padding: 20px;
  height: fit-content;
  position: sticky;
  top: 24px;
}

.templates-list h2 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #1a1a1a;
}

.list-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.list-item {
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.list-item:hover {
  border-color: #0066cc;
  background: #f9f9f9;
}

.list-item.active {
  border-color: #0066cc;
  background: #e6f2ff;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.item-header h3 {
  margin: 0;
  font-size: 14px;
  color: #1a1a1a;
}

.item-date {
  font-size: 12px;
  color: #999;
}

.item-desc {
  margin: 0 0 8px 0;
  font-size: 12px;
  color: #666;
  line-height: 1.4;
}

.item-template {
  font-size: 11px;
  color: #0066cc;
  background: #e6f2ff;
  padding: 4px 8px;
  border-radius: 3px;
  display: inline-block;
}

.edit-panel {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.panel-header h2 {
  margin: 0;
  font-size: 20px;
}

.panel-actions {
  display: flex;
  gap: 12px;
}

.panel-content {
  padding: 20px;
}

.info-section,
.style-section,
.nav-section {
  margin-bottom: 32px;
}

.info-section h3,
.style-section h3,
.nav-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #1a1a1a;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 12px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.info-item label {
  display: block;
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
  font-weight: 500;
}

.info-item p {
  margin: 0;
  font-size: 14px;
  color: #1a1a1a;
}

.site-path {
  font-family: monospace;
  background: #f5f5f5;
  padding: 4px 8px;
  border-radius: 3px;
  display: inline-block;
}

.site-link {
  color: #0066cc;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s;
}

.site-link:hover {
  color: #0052a3;
  text-decoration: underline;
}

.colors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.color-item label {
  display: block;
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
  font-weight: 500;
}

.color-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-box {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.color-display span {
  font-size: 13px;
  color: #1a1a1a;
  font-family: monospace;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item-display {
  padding: 12px;
  background: #f9f9f9;
  border-radius: 4px;
  border-left: 3px solid #0066cc;
}

.nav-item-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.nav-name {
  font-weight: 500;
  color: #1a1a1a;
}

.nav-route {
  font-size: 12px;
  color: #666;
  font-family: monospace;
}

.nav-children {
  font-size: 12px;
  color: #0066cc;
  background: #e6f2ff;
  padding: 2px 8px;
  border-radius: 3px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  font-size: 13px;
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

.btn-danger {
  background: #ff4d4f;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #ff7875;
}

.btn-small {
  padding: 6px 12px;
  font-size: 12px;
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
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
}

.modal-small {
  max-width: 400px;
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

.form-textarea {
  resize: vertical;
}

.form-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e0e0e0;
}

.form-section h3 {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: #1a1a1a;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
}

.color-inputs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.color-input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.color-input-group label {
  font-size: 12px;
  margin: 0;
}

.color-picker {
  width: 100%;
  height: 40px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
}

.nav-edit-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.nav-edit-item {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 4px;
}

.nav-edit-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-edit-info .form-input {
  margin: 0;
}

.nav-edit-actions {
  display: flex;
  gap: 8px;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
}
</style>
