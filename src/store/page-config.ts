// defineStore：Pinia store 工厂函数，用于创建 page-config 状态模块
import { defineStore } from 'pinia';
// ref：创建响应式引用
import { ref } from 'vue';

export interface PageNavItem {
  name: string;
  route: string;
  children?: PageNavItem[];
}

export interface PageConfig {
  id: string;
  title: string;
  body: {
    route: string;
    children: PageNavItem[];
  };
  createdAt: string;
  updatedAt: string;
}

export const usePageConfigStore = defineStore('page-config', () => {
  const pages = ref<PageConfig[]>([]);

  // 添加页面
  const addPage = (config: Omit<PageConfig, 'id' | 'createdAt' | 'updatedAt'>) => {
    const newPage: PageConfig = {
      ...config,
      id: Date.now().toString(),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    pages.value.push(newPage);
    saveToLocalStorage();
    return newPage;
  };

  // 更新页面
  const updatePage = (id: string, config: Partial<PageConfig>) => {
    const index = pages.value.findIndex(p => p.id === id);
    if (index !== -1) {
      const currentPage = pages.value[index];
      if (!currentPage) return null;
      
      pages.value[index] = {
        id: currentPage.id,
        title: config.title ?? currentPage.title,
        body: config.body ?? currentPage.body,
        createdAt: currentPage.createdAt,
        updatedAt: new Date().toISOString(),
      };
      saveToLocalStorage();
      return pages.value[index];
    }
    return null;
  };

  // 删除页面
  const deletePage = (id: string) => {
    const index = pages.value.findIndex(p => p.id === id);
    if (index !== -1) {
      pages.value.splice(index, 1);
      saveToLocalStorage();
      return true;
    }
    return false;
  };

  // 获取页面
  const getPage = (id: string) => {
    return pages.value.find(p => p.id === id);
  };

  // 保存到本地存储
  const saveToLocalStorage = () => {
    localStorage.setItem('vben-page-configs', JSON.stringify(pages.value));
  };

  // 从本地存储加载
  const loadFromLocalStorage = () => {
    const stored = localStorage.getItem('vben-page-configs');
    if (stored) {
      try {
        pages.value = JSON.parse(stored);
      } catch (e) {
        console.error('Failed to load page configs:', e);
      }
    }
  };

  // 初始化时加载
  loadFromLocalStorage();

  const $reset = () => {
    pages.value = [];
    localStorage.removeItem('vben-page-configs');
  };

  return {
    $reset,
    pages,
    addPage,
    updatePage,
    deletePage,
    getPage,
  };
});

