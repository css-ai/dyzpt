// preferences：全局偏好设置，用于获取当前语言（Accept-Language 请求头）
import { preferences } from '@vben/preferences';
// useAccessStore：获取当前 accessToken，用于手动构造鉴权请求头
import { useAccessStore } from '@vben/stores';

// baseRequestClient：不自动注入 token 的基础请求客户端，此处手动拼接 Authorization 头
import { baseRequestClient } from '#/api/request';

// 引入站点页面相关的前端类型定义
import type { GeneratedTemplate, NavItem, TemplateConfig } from '#/store/template';

interface ResponseEnvelope<T> {
  code: number;
  data: T;
  message?: string;
}

interface BackendSitePage {
  id: string;
  owner_username: string;
  site_path: string;
  bind_domain: string;
  site_name: string;
  site_description: string;
  template_id: string;
  nav_items: NavItem[];
  colors: TemplateConfig['colors'];
  fonts: TemplateConfig['fonts'];
  status: 'draft' | 'published';
  created_at: string;
  updated_at: string;
}

export interface CreateSitePageParams {
  domain: string;
  navItems: NavItem[];
  siteDescription: string;
  siteName: string;
  templateId: string;
  templateName: string;
  colors: TemplateConfig['colors'];
  fonts: TemplateConfig['fonts'];
}

export interface UpdateSitePageParams {
  domain?: string;
  navItems?: NavItem[];
  siteDescription?: string;
  siteName?: string;
  colors?: TemplateConfig['colors'];
  fonts?: TemplateConfig['fonts'];
}

function getAuthHeaders() {
  const accessStore = useAccessStore();
  const token = accessStore.accessToken;
  return {
    Authorization: token ? `Bearer ${token}` : '',
    'Accept-Language': preferences.app.locale,
  };
}

function toFrontend(data: BackendSitePage): GeneratedTemplate {
  return {
    id: data.id,
    templateId: data.template_id,
    templateName: data.template_id,
    siteName: data.site_name,
    siteDescription: data.site_description,
    domain: data.bind_domain,
    navItems: data.nav_items,
    colors: data.colors,
    fonts: data.fonts,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

function unwrapResponse<T>(payload: any): T {
  let result = payload;

  // 兼容 axios/raw response: { data, status, headers, ... }
  if (
    result &&
    typeof result === 'object' &&
    'data' in result &&
    ('status' in result || 'headers' in result || 'config' in result)
  ) {
    result = result.data;
  }

  // 兼容业务包裹格式: { code, data, message }
  if (
    result &&
    typeof result === 'object' &&
    'code' in result &&
    'data' in result
  ) {
    result = (result as ResponseEnvelope<T>).data;
  }

  return result as T;
}

/** 获取当前用户可管理的页面 */
export async function getMySitePagesApi() {
  const payload = await baseRequestClient.get('/site-pages', {
    headers: getAuthHeaders(),
  });
  const data = unwrapResponse<BackendSitePage[]>(payload);
  return Array.isArray(data) ? data.map(toFrontend) : [];
}

/** 根据域名查询页面（公开访问） */
export async function getSitePageByDomainApi(domain: string) {
  const payload = await baseRequestClient.get(
    `/public/site-pages/domain/${encodeURIComponent(domain)}`,
  );
  return toFrontend(unwrapResponse<BackendSitePage>(payload));
}

/** 创建页面 */
export async function createSitePageApi(data: CreateSitePageParams) {
  const payload = {
    site_path: data.domain,
    bind_domain: data.domain,
    site_name: data.siteName,
    site_description: data.siteDescription,
    template_id: data.templateId,
    nav_items: data.navItems,
    colors: data.colors,
    fonts: data.fonts,
    status: 'published' as const,
  };
  const createdPayload = await baseRequestClient.post('/site-pages', payload, {
    headers: getAuthHeaders(),
  });
  return toFrontend(unwrapResponse<BackendSitePage>(createdPayload));
}

/** 更新页面 */
export async function updateSitePageApi(id: string, data: UpdateSitePageParams) {
  const payload = {
    bind_domain: data.domain,
    site_name: data.siteName,
    site_description: data.siteDescription,
    nav_items: data.navItems,
    colors: data.colors,
    fonts: data.fonts,
  };
  const updatedPayload = await baseRequestClient.put(`/site-pages/${id}`, payload, {
    headers: getAuthHeaders(),
  });
  return toFrontend(unwrapResponse<BackendSitePage>(updatedPayload));
}

/** 删除页面 */
export async function deleteSitePageApi(id: string) {
  const payload = await baseRequestClient.delete(`/site-pages/${id}`, {
    headers: getAuthHeaders(),
  });
  return unwrapResponse<boolean>(payload);
}
