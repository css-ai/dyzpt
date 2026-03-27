// UserInfo：用户信息类型定义（包含用户名、真实姓名、角色、头像等）
import type { UserInfo } from '@vben/types';

// requestClient：携带 accessToken 的标准鉴权请求客户端
import { requestClient } from '#/api/request';

/**
 * 获取用户信息
 */
export async function getUserInfoApi() {
  return requestClient.get<UserInfo>('/user/info');
}
