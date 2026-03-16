import { defineStore } from 'pinia';
import { ref } from 'vue';
import { template1Config } from '#/views/templates/template-1/config';
import { template2Config } from '#/views/templates/template-2/config';
import { template3Config } from '#/views/templates/template-3/config';

export interface NavItem {
  name: string;
  route: string;
  icon?: string;
  children?: NavItem[];
}

export interface TemplateConfig {
  id: string;
  name: string;
  description: string;
  thumbnail: string;
  category: string;
  navItems: NavItem[];
  colors: {
    primary: string;
    secondary: string;
    background: string;
    text: string;
  };
  fonts: {
    heading: string;
    body: string;
  };
}

export interface GeneratedTemplate {
  id: string;
  templateId: string;
  templateName: string;
  siteName: string;
  siteDescription: string;
  sitePath: string;
  navItems: NavItem[];
  colors: TemplateConfig['colors'];
  fonts: TemplateConfig['fonts'];
  createdAt: string;
  updatedAt: string;
}

export const useTemplateStore = defineStore('template', () => {
  // 所有可用的模板
  const availableTemplates = ref<TemplateConfig[]>([
    template1Config,
    template2Config,
    template3Config,
  ]);

  // 已生成的模板
  const generatedTemplates = ref<GeneratedTemplate[]>([]);

  // 获取所有可用模板
  const getAvailableTemplates = () => {
    return availableTemplates.value;
  };

  // 获取单个模板
  const getTemplate = (id: string) => {
    return availableTemplates.value.find(t => t.id === id);
  };

  // 生成新模板
  const generateTemplate = (
    templateId: string,
    siteName: string,
    siteDescription: string,
    sitePath: string,
  ) => {
    const template = getTemplate(templateId);
    if (!template) return null;

    const newGenerated: GeneratedTemplate = {
      id: `generated-${Date.now()}`,
      templateId,
      templateName: template.name,
      siteName,
      siteDescription,
      sitePath,
      navItems: JSON.parse(JSON.stringify(template.navItems)),
      colors: { ...template.colors },
      fonts: { ...template.fonts },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    generatedTemplates.value.push(newGenerated);
    saveToLocalStorage();
    return newGenerated;
  };

  // 获取所有已生成的模板
  const getGeneratedTemplates = () => {
    return generatedTemplates.value;
  };

  // 获取单个已生成的模板
  const getGeneratedTemplate = (id: string) => {
    return generatedTemplates.value.find(t => t.id === id);
  };

  // 通过网站路径获取模板
  const getGeneratedTemplateByPath = (path: string) => {
    return generatedTemplates.value.find(t => t.sitePath === path);
  };

  // 更新已生成的模板
  const updateGeneratedTemplate = (
    id: string,
    updates: Partial<Omit<GeneratedTemplate, 'id' | 'createdAt' | 'updatedAt'>>,
  ) => {
    const index = generatedTemplates.value.findIndex(t => t.id === id);
    if (index !== -1) {
      const currentTemplate = generatedTemplates.value[index];
      if (!currentTemplate) return null;
      
      generatedTemplates.value[index] = {
        ...currentTemplate,
        ...updates,
        id: currentTemplate.id,
        createdAt: currentTemplate.createdAt,
        updatedAt: new Date().toISOString(),
      };
      saveToLocalStorage();
      return generatedTemplates.value[index];
    }
    return null;
  };

  // 删除已生成的模板
  const deleteGeneratedTemplate = (id: string) => {
    const index = generatedTemplates.value.findIndex(t => t.id === id);
    if (index !== -1) {
      generatedTemplates.value.splice(index, 1);
      saveToLocalStorage();
      return true;
    }
    return false;
  };

  // 保存到本地存储
  const saveToLocalStorage = () => {
    localStorage.setItem('vben-generated-templates', JSON.stringify(generatedTemplates.value));
  };

  // 从本地存储加载
  const loadFromLocalStorage = () => {
    const stored = localStorage.getItem('vben-generated-templates');
    if (stored) {
      try {
        generatedTemplates.value = JSON.parse(stored);
      } catch (e) {
        console.error('Failed to load generated templates:', e);
      }
    }
  };

  // 初始化时加载
  loadFromLocalStorage();

  return {
    availableTemplates,
    generatedTemplates,
    getAvailableTemplates,
    getTemplate,
    generateTemplate,
    getGeneratedTemplates,
    getGeneratedTemplate,
    getGeneratedTemplateByPath,
    updateGeneratedTemplate,
    deleteGeneratedTemplate,
  };
});

