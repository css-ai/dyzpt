// requestClient：携带 accessToken 的标准请求客户端，用于需要鉴权的接口
// baseRequestClient：基础请求客户端（不自动注入 token），用于登录、刷新 token 等无鉴权接口
import { baseRequestClient, requestClient } from '#/api/request';

export namespace AuthApi {
  /** 登录接口参数 */
  export interface LoginParams {
    password?: string;
    username?: string;
  }

  /** 注册接口参数 */
  export interface RegisterParams {
    username: string;
    password: string;
    register_key: string;
  }

  /** 创建注册密钥的参数 */
  export interface RegisterKeyCreateParams {
    role: 'admin' | 'super' | 'user';
  }

  /** 注册密钥详情 */
  export interface RegisterKeyResult {
    id: string;
    registerKey: string;
    role: 'admin' | 'super' | 'user';
    createdBy: string;
    createdAt: string;
    expiresAt: string | null;
    usedBy: string | null;
    usedAt: string | null;
    expired: boolean;
  }

  /** 注册统计结果 */
  export interface RegisterStatsResult {
    totalUsers: number;
    adminUsers: number;
    superUsers: number;
  }

  /** 用户管理列表项 */
  export interface UserManageItem {
    userId: string;
    username: string;
    realName: string;
    roles: string[];
    createdAt: string;
    pageCount: number;
    quota: UserQuota;
  }

  /** 用户页面配额信息 */
  export interface UserQuota {
    planType?: 'free' | 'basic' | 'pro' | 'enterprise';
    maxPages: number;
    startDate: string | null;
    endDate: string | null;
  }

  /** 套餐项 */
  export interface PlanItem {
    planType: 'free' | 'basic' | 'pro' | 'enterprise';
    name: string;
    maxPages: number;
    durationDays: number;
  }

  /** 充值订单创建结果（含 Native 二维码链接） */
  export interface RechargeOrderResult {
    orderId: string;
    codeUrl: string;
    planType: 'free' | 'basic' | 'pro' | 'enterprise';
    planName: string;
  }

  /** 充值订单状态查询结果 */
  export interface RechargeOrderStatus {
    orderId: string;
    planType: 'free' | 'basic' | 'pro' | 'enterprise';
    status: 'pending' | 'paid';
    createdAt: string;
    quota: UserQuota | null;
  }

  /** 管理员更新用户套餐参数 */
  export interface UserPlanUpdateParams {
    plan_type: 'free' | 'basic' | 'pro' | 'enterprise';
  }

  /** 用户名下的页面列表项 */
  export interface UserPageItem {
    id: string;
    siteName: string;
    bindDomain: string;
    status: 'draft' | 'published';
    createdAt: string;
  }

  /** 修改用户密码的参数 */
  export interface UserPasswordUpdateParams {
    password: string;
  }

  /** 更新用户配额的参数 */
  export interface UserQuotaUpdateParams {
    max_pages: number;
    start_date: string | null;
    end_date: string | null;
  }

  /** 忘记密码（通过注册密钥重置）参数 */
  export interface ResetPasswordParams {
    username: string;
    register_key: string;
    new_password: string;
    confirm_password: string;
  }

  /** 更新密钥有效期的参数 */
  export interface RegisterKeyUpdateExpiresParams {
    expires_at: string | null;
  }

  /** 操作日志单条记录 */
  export interface OperationLog {
    id: string;
    operator: string;
    action: string;
    target: string;
    detail: string;
    createdAt: string;
  }

  /** 操作日志分页结果 */
  export interface OperationLogsResult {
    total: number;
    page: number;
    pageSize: number;
    list: OperationLog[];
  }

  /** 域名验证结果 */
  export interface DomainVerifyResult {
    domain: string;
    resolvedIp: string | null;
    resolvable: boolean;
    conflict?: boolean;
    siteName?: string;
  }

  /** 批量删除操作结果（区分成功删除与跳过） */
  export interface BatchDeleteResult {
    deleted: string[];
    skipped: string[];
  }

  /** 回收站条目 */
  export interface TrashItem {
    id: string;
    /** 条目类型：用户 / 页面 / 密钥 */
    itemType: 'user' | 'page' | 'key';
    itemId: string;
    /** 被删除对象的原始数据快照 */
    itemData: Record<string, any>;
    deletedBy: string;
    deletedAt: string;
    expireAt: string;
  }

  /** 登录接口返回值 */
  export interface LoginResult {
    accessToken: string;
  }

  /** 刷新 Token 返回值 */
  export interface RefreshTokenResult {
    data: string;
    status: number;
  }
}

/**
 * 用户登录
 * @param data 登录参数（用户名 + 密码）
 * @returns 包含 accessToken 的登录结果
 */
export async function loginApi(data: AuthApi.LoginParams) {
  return requestClient.post<AuthApi.LoginResult>('/auth/login', data);
}

/**
 * 用户注册
 * @param data 注册参数（用户名、密码、注册密钥）
 * @returns 注册是否成功
 */
export async function registerApi(data: AuthApi.RegisterParams) {
  return requestClient.post<boolean>('/auth/register', data);
}

/**
 * 忘记密码 —— 通过注册密钥重置密码
 * @param data 包含用户名、注册密钥、新密码及确认密码
 * @returns 重置是否成功
 */
export async function resetPasswordApi(data: AuthApi.ResetPasswordParams) {
  return requestClient.post<boolean>('/auth/reset-password', data);
}

/**
 * 生成注册密钥（仅管理员可调用）
 * @param data 指定新密钥对应的角色
 * @returns 新生成的注册密钥详情
 */
export async function createRegisterKeyApi(data: AuthApi.RegisterKeyCreateParams) {
  return requestClient.post<AuthApi.RegisterKeyResult>('/auth/register-keys', data);
}

/**
 * 获取注册密钥列表，支持按角色、使用状态、关键词筛选
 * @param params.role    筛选角色（admin / super / user）
 * @param params.used    筛选使用状态（'yes' 已使用 / 'no' 未使用）
 * @param params.keyword 关键词模糊搜索
 * @returns 密钥列表
 */
export async function getRegisterKeysApi(params?: {
  role?: string;
  used?: 'yes' | 'no';
  keyword?: string;
}) {
  return requestClient.get<AuthApi.RegisterKeyResult[]>('/auth/register-keys', { params });
}

/**
 * 删除指定注册密钥
 * @param keyId 要删除的密钥 ID
 * @returns 删除是否成功
 */
export async function deleteRegisterKeyApi(keyId: string) {
  return requestClient.delete<boolean>(`/auth/register-keys/${keyId}`);
}

/**
 * 更新指定注册密钥的有效期
 * @param keyId 密钥 ID
 * @param data  新的过期时间（null 表示永不过期）
 * @returns 更新后的过期时间
 */
export async function updateRegisterKeyExpiresApi(
  keyId: string,
  data: AuthApi.RegisterKeyUpdateExpiresParams,
) {
  return requestClient.put<{ expiresAt: string | null }>(
    `/auth/register-keys/${keyId}/expires`,
    data,
  );
}

/**
 * 获取套餐列表
 */
export async function getPlansApi() {
  return requestClient.get<AuthApi.PlanItem[]>('/auth/plans');
}

/**
 * 用户创建充值订单，返回 Native 二维码链接（code_url）
 * 演示环境返回 mock code_url，生产环境替换为微信真实下单结果
 */
export async function createRechargeOrderApi(data: { plan_type: AuthApi.PlanItem['planType'] }) {
  return requestClient.post<AuthApi.RechargeOrderResult>('/auth/recharge-orders', data);
}

/**
 * 查询充值订单状态（前端轮询用）
 * @param orderId 订单 ID
 */
export async function getRechargeOrderApi(orderId: string) {
  return requestClient.get<AuthApi.RechargeOrderStatus>(`/auth/recharge-orders/${orderId}`);
}

/**
 * 演示环境：模拟支付成功（点击"我已完成支付"触发）
 * 生产环境中由微信服务器回调 notify_url，此接口不对外暴露
 * @param orderId 订单 ID
 */
export async function mockPayOrderApi(orderId: string) {
  return requestClient.post<AuthApi.UserQuota>(`/auth/recharge-orders/${orderId}/mock-pay`, {});
}

/**
 * 管理员直接修改用户套餐
 */
export async function updateUserPlanApi(userId: string, data: AuthApi.UserPlanUpdateParams) {
  return requestClient.put<AuthApi.UserQuota>(`/auth/users/${userId}/plan`, data);
}

/**
 * 获取注册统计数据（总用户数、各角色人数）
 * @returns 注册统计结果
 */
export async function getRegisterStatsApi() {
  return requestClient.get<AuthApi.RegisterStatsResult>('/auth/register-stats');
}

/**
 * 获取用户列表（管理员专用），支持按关键词和角色筛选
 * @param params.keyword 用户名关键词
 * @param params.role    角色筛选
 * @returns 用户列表
 */
export async function getUsersApi(params?: { keyword?: string; role?: string }) {
  return requestClient.get<AuthApi.UserManageItem[]>('/auth/users', { params });
}

/**
 * 修改指定用户的密码（管理员操作）
 * @param userId 目标用户 ID
 * @param data   包含新密码
 * @returns 修改是否成功
 */
export async function updateUserPasswordApi(
  userId: string,
  data: AuthApi.UserPasswordUpdateParams,
) {
  return requestClient.put<boolean>(`/auth/users/${userId}/password`, data);
}

/**
 * 删除指定用户（软删除，进入回收站）
 * @param userId 要删除的用户 ID
 * @returns 删除是否成功
 */
export async function deleteUserApi(userId: string) {
  return requestClient.delete<boolean>(`/auth/users/${userId}`);
}

/**
 * 批量删除用户（软删除，进入回收站）
 * @param userIds 要删除的用户 ID 数组
 * @returns 批量删除结果（包含成功和跳过的 ID 列表）
 */
export async function batchDeleteUsersApi(userIds: string[]) {
  return requestClient.post<AuthApi.BatchDeleteResult>('/auth/users/batch-delete', {
    user_ids: userIds,
  });
}

/**
 * 获取指定用户名下的所有页面
 * @param userId 目标用户 ID
 * @returns 该用户的页面列表
 */
export async function getUserPagesApi(userId: string) {
  return requestClient.get<AuthApi.UserPageItem[]>(`/auth/users/${userId}/pages`);
}

/**
 * 管理员删除指定页面（软删除，进入回收站）
 * @param pageId 要删除的页面 ID
 * @returns 删除是否成功
 */
export async function deletePageByAdminApi(pageId: string) {
  return requestClient.delete<boolean>(`/site-pages/${pageId}`);
}

/**
 * 切换页面展示状态（published <-> draft）
 * @param pageId 目标页面 ID
 * @returns 更新后的页面状态
 */
export async function togglePageStatusApi(pageId: string) {
  return requestClient.put<{ status: 'draft' | 'published' }>(
    `/auth/pages/${pageId}/status`,
    {},
  );
}

/**
 * 获取指定用户的页面配额信息
 * @param userId 目标用户 ID
 * @returns 用户配额（最大页面数、有效期起止时间）
 */
export async function getUserQuotaApi(userId: string) {
  return requestClient.get<AuthApi.UserQuota>(`/auth/users/${userId}/quota`);
}

/**
 * 更新指定用户的页面配额
 * @param userId 目标用户 ID
 * @param data   新的配额参数（最大页面数、有效期起止时间）
 * @returns 更新后的配额信息
 */
export async function updateUserQuotaApi(
  userId: string,
  data: AuthApi.UserQuotaUpdateParams,
) {
  return requestClient.put<AuthApi.UserQuota>(`/auth/users/${userId}/quota`, data);
}

/**
 * 获取操作日志列表，支持分页和按操作人/动作类型筛选
 * @param params.page       当前页码
 * @param params.page_size  每页条数
 * @param params.operator   操作人用户名筛选
 * @param params.action     动作类型筛选
 * @returns 分页操作日志结果
 */
export async function getOperationLogsApi(params?: {
  page?: number;
  page_size?: number;
  operator?: string;
  action?: string;
}) {
  return requestClient.get<AuthApi.OperationLogsResult>('/auth/logs', { params });
}

/**
 * 获取回收站列表，可按类型筛选
 * @param params.item_type 筛选类型（user / page / key），不传则返回全部
 * @returns 回收站条目列表
 */
export async function getTrashApi(params?: { item_type?: string }) {
  return requestClient.get<AuthApi.TrashItem[]>('/auth/trash', { params });
}

/**
 * 从回收站恢复指定条目
 * @param trashId 回收站记录 ID
 * @returns 恢复是否成功
 */
export async function restoreTrashApi(trashId: string) {
  return requestClient.post<boolean>(`/auth/trash/${trashId}/restore`, {});
}

/**
 * 彻底删除回收站中的指定条目（不可恢复）
 * @param trashId 回收站记录 ID
 * @returns 删除是否成功
 */
export async function purgeTrashApi(trashId: string) {
  return requestClient.delete<boolean>(`/auth/trash/${trashId}`);
}

/**
 * 清空整个回收站（所有条目永久删除，不可恢复）
 * @returns 包含已清除条目数量的结果
 */
export async function clearTrashApi() {
  return requestClient.delete<{ cleared: number }>('/auth/trash');
}

/**
 * 验证域名是否可解析及是否存在冲突
 * @param domain 要验证的域名
 * @returns 域名验证结果（可解析性、IP、冲突信息）
 */
export async function verifyDomainApi(domain: string) {
  return requestClient.get<AuthApi.DomainVerifyResult>('/public/verify-domain', {
    params: { domain },
  });
}

/**
 * 刷新 accessToken（使用 refreshToken cookie 静默续期）
 * @returns 新的 accessToken 及状态码
 */
export async function refreshTokenApi() {
  return baseRequestClient.post<AuthApi.RefreshTokenResult>('/auth/refresh', {
    withCredentials: true,
  });
}

/**
 * 退出登录（清除服务端 refreshToken cookie）
 */
export async function logoutApi() {
  return baseRequestClient.post('/auth/logout', {
    withCredentials: true,
  });
}

/**
 * 获取当前用户的权限码列表（用于前端按钮级权限控制）
 * @returns 权限码字符串数组
 */
export async function getAccessCodesApi() {
  return requestClient.get<string[]>('/auth/codes');
}
