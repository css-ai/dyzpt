// defineStore：Pinia store 工厂函数
import { defineStore } from 'pinia';
// ref：创建响应式引用
import { ref } from 'vue';

// 站点页面相关 API 接口
import {
  createSitePageApi,      // 创建新站点页面
  deleteSitePageApi,      // 删除站点页面
  getMySitePagesApi,      // 获取当前用户的站点页面列表
  getSitePageByDomainApi, // 通过域名查询站点页面
  updateSitePageApi,      // 更新站点页面信息
} from '#/api';
// 用户 store，用于获取当前登录用户信息（角色、配额等）
import { useUserStore } from '@vben/stores';
// 三套内置模板的配置（包含导航、颜色、字体等元数据）
import { template1Config } from '#/views/templates/template-1/config';
import { template2Config } from '#/views/templates/template-2/config';
import { template3Config } from '#/views/templates/template-3/config';

/** 导航栏菜单项结构 */
export interface NavItem {
  name: string;
  route: string;
  icon?: string;
  children?: NavItem[];
}

/** 模板配置结构（系统内置模板的元数据） */
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

/** 用户已生成的站点页面结构 */
export interface GeneratedTemplate {
  id: string;
  templateId: string;
  templateName: string;
  siteName: string;
  siteDescription: string;
  domain: string;
  navItems: NavItem[];
  colors: TemplateConfig['colors'];
  fonts: TemplateConfig['fonts'];
  createdAt: string;
  updatedAt: string;
}

/**
 * 规范化域名：去除首尾空格并转为小写
 * @param domain 原始域名字符串
 */
function normalizeDomain(domain: string) {
  return domain.trim().toLowerCase();
}

/**
 * 判断当前登录用户是否为管理员（admin 或 super 角色）
 */
function isAdminUser() {
  const userStore = useUserStore();
  const roles = userStore.userInfo?.roles ?? [];
  return roles.some((role) => ['admin', 'super'].includes(role.toLowerCase()));
}

/**
 * 获取当前用户的页面配额信息
 * @returns { maxPages } 最大可创建页面数，-1 表示无限制
 */
function getUserPageQuota(): { maxPages: number } {
  const userStore = useUserStore();
  const info = userStore.userInfo as any;
  return info?.pageQuota ?? { maxPages: 1 };
}

export const useTemplateStore = defineStore('template', () => {
  /** 系统内置可用模板列表 */
  const availableTemplates = ref<TemplateConfig[]>([
    template1Config,
    template2Config,
    template3Config,
  ]);

  /** 当前用户已生成的站点页面列表 */
  const generatedTemplates = ref<GeneratedTemplate[]>([]);

  /** 全局加载状态 */
  const loading = ref(false);

  /**
   * 获取所有可用模板列表
   */
  const getAvailableTemplates = () => availableTemplates.value;

  /**
   * 根据模板 ID 查找指定模板
   * @param id 模板 ID
   */
  const getTemplate = (id: string) => {
    return availableTemplates.value.find((t) => t.id === id);
  };

  /**
   * 获取当前用户所有已生成的站点页面
   */
  const getGeneratedTemplates = () => generatedTemplates.value;

  /**
   * 根据 ID 查找已生成的站点页面
   * @param id 站点页面 ID
   */
  const getGeneratedTemplate = (id: string) => {
    return generatedTemplates.value.find((t) => t.id === id);
  };

  /**
   * 根据域名查找已生成的站点页面（域名匹配时忽略大小写和首尾空格）
   * @param domain 目标域名
   */
  const getGeneratedTemplateByDomain = (domain: string) => {
    const targetDomain = normalizeDomain(domain);
    return generatedTemplates.value.find(
      (t) => normalizeDomain(t.domain) === targetDomain,
    );
  };

  /**
   * 判断当前用户是否还能继续创建新页面
   * - admin/super 角色无限制
   * - 普通用户受 pageQuota.maxPages 约束
   * - maxPages 为 -1 时视为无限制
   */
  const canCreateMore = () => {
    if (isAdminUser()) return true;
    const quota = getUserPageQuota();
    const maxPages = quota.maxPages;
    if (maxPages === -1) return true;  // 无限
    return generatedTemplates.value.length < maxPages;
  };

  /**
   * 从后端加载当前用户的所有站点页面，并写入 generatedTemplates
   * 会自动规范化每条记录的 domain 字段
   */
  const loadMyGeneratedTemplates = async () => {
    loading.value = true;
    try {
      const data = await getMySitePagesApi();
      generatedTemplates.value = data.map((item) => ({
        ...item,
        domain: normalizeDomain(item.domain || ''),
      }));
    } finally {
      loading.value = false;
    }
  };

  /**
   * 基于指定模板生成一个新站点页面并保存到后端
   * @param templateId    要使用的模板 ID
   * @param siteName      站点名称
   * @param siteDescription 站点描述
   * @param domain        站点绑定域名
   * @throws 超出配额、模板不存在、域名为空时抛出 Error
   */
  const generateTemplate = async (
    templateId: string,
    siteName: string,
    siteDescription: string,
    domain: string,
  ) => {
    if (!canCreateMore()) {
      const quota = getUserPageQuota();
      throw new Error(`当前账号最多只能生成 ${quota.maxPages} 个页面，请联系管理员扩容权限`);
    }

    const template = getTemplate(templateId);
    if (!template) {
      throw new Error('模板不存在');
    }

    const payloadDomain = normalizeDomain(domain);
    if (!payloadDomain) {
      throw new Error('域名不能为空');
    }

    // 调用后端接口创建站点页面
    const created = await createSitePageApi({
      templateId,
      templateName: template.name,
      siteName,
      siteDescription,
      domain: payloadDomain,
      navItems: JSON.parse(JSON.stringify(template.navItems)), // 深拷贝导航项
      colors: { ...template.colors },
      fonts: { ...template.fonts },
    });

    // 将新创建的页面插入列表头部，保持最新的在最前
    generatedTemplates.value.unshift({
      ...created,
      domain: normalizeDomain(created.domain),
    });

    return created;
  };

  /**
   * 更新已生成站点页面的部分字段
   * @param id      要更新的站点页面 ID
   * @param updates 需要更新的字段（排除 id / createdAt / updatedAt）
   */
  const updateGeneratedTemplate = async (
    id: string,
    updates: Partial<Omit<GeneratedTemplate, 'id' | 'createdAt' | 'updatedAt'>>,
  ) => {
    // 如果更新中包含 domain，也进行规范化处理
    const payload = {
      ...updates,
      domain: updates.domain ? normalizeDomain(updates.domain) : undefined,
    };

    const updated = await updateSitePageApi(id, payload);
    const index = generatedTemplates.value.findIndex((t) => t.id === id);

    // 更新本地缓存中对应的条目
    if (index !== -1) {
      generatedTemplates.value[index] = {
        ...updated,
        domain: normalizeDomain(updated.domain),
      };
    }

    return updated;
  };

  /**
   * 删除指定站点页面（同时从后端和本地缓存中移除）
   * @param id 要删除的站点页面 ID
   */
  const deleteGeneratedTemplate = async (id: string) => {
    await deleteSitePageApi(id);
    const index = generatedTemplates.value.findIndex((t) => t.id === id);
    if (index !== -1) {
      generatedTemplates.value.splice(index, 1);
    }
  };

  /**
   * 通过域名获取站点页面详情
   * - 优先从本地缓存查找，命中则直接返回，避免重复请求
   * - 未命中则调用后端接口获取
   * @param domain 目标域名
   */
  const fetchTemplateByDomain = async (domain: string) => {
    const target = normalizeDomain(domain);
    const cached = getGeneratedTemplateByDomain(target);
    if (cached) {
      return cached;
    }

    const data = await getSitePageByDomainApi(target);
    return {
      ...data,
      domain: normalizeDomain(data.domain),
    };
  };

  /**
   * 重置 store 状态（退出登录时调用）
   * 清空已生成页面列表并重置加载状态
   */
  const $reset = () => {
    generatedTemplates.value = [];
    loading.value = false;
  };

  return {
    $reset,
    availableTemplates,
    generatedTemplates,
    loading,
    getAvailableTemplates,
    getTemplate,
    getGeneratedTemplates,
    getGeneratedTemplate,
    getGeneratedTemplateByDomain,
    canCreateMore,
    loadMyGeneratedTemplates,
    generateTemplate,
    updateGeneratedTemplate,
    deleteGeneratedTemplate,
    fetchTemplateByDomain,
  };
});
