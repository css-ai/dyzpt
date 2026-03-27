// RouteRecordStringComponent：路由记录类型（组件路径为字符串形式，由后端动态下发）
import type { RouteRecordStringComponent } from '@vben/types';

// requestClient：携带 accessToken 的标准鉴权请求客户端
import { requestClient } from '#/api/request';

/**
 * 获取用户所有菜单
 */
export async function getAllMenusApi() {
  return requestClient.get<RouteRecordStringComponent[]>('/menu/all');
}
