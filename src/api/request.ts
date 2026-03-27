/**
 * 该文件可自行根据业务逻辑进行调整
 * 负责创建和配置全局 HTTP 请求客户端，包含 Token 注入、Token 刷新、错误拦截等逻辑
 */
// RequestClientOptions：请求客户端配置项类型
import type { RequestClientOptions } from '@vben/request';

// useAppConfig：读取应用配置（如 apiURL）
import { useAppConfig } from '@vben/hooks';
// preferences：全局偏好设置（语言、登录过期模式等）
import { preferences } from '@vben/preferences';
import {
  authenticateResponseInterceptor,  // Token 鉴权失败拦截器（处理 401）
  defaultResponseInterceptor,        // 统一响应数据格式解包拦截器
  errorMessageResponseInterceptor,   // 通用错误消息拦截器
  RequestClient,                     // 底层 HTTP 客户端类
} from '@vben/request';
// useAccessStore：管理 accessToken 及登录过期状态
import { useAccessStore } from '@vben/stores';

// message：Ant Design Vue 全局轻提示
import { message } from 'ant-design-vue';

// useAuthStore：业务层鉴权 store（退出登录等）
import { useAuthStore } from '#/store';

// refreshTokenApi：用于静默刷新 accessToken 的接口
import { refreshTokenApi } from './core';

const { apiURL } = useAppConfig(import.meta.env, import.meta.env.PROD);

function createRequestClient(baseURL: string, options?: RequestClientOptions) {
  const client = new RequestClient({
    ...options,
    baseURL,
  });

  /**
   * 重新认证逻辑
   */
  async function doReAuthenticate() {
    console.warn('Access token or refresh token is invalid or expired. ');
    const accessStore = useAccessStore();
    const authStore = useAuthStore();
    accessStore.setAccessToken(null);
    if (
      preferences.app.loginExpiredMode === 'modal' &&
      accessStore.isAccessChecked
    ) {
      accessStore.setLoginExpired(true);
    } else {
      await authStore.logout();
    }
  }

  /**
   * 刷新token逻辑
   */
  async function doRefreshToken() {
    const accessStore = useAccessStore();
    const resp = await refreshTokenApi();
    const newToken = resp.data;
    accessStore.setAccessToken(newToken);
    return newToken;
  }

  function formatToken(token: null | string) {
    return token ? `Bearer ${token}` : null;
  }

  // 请求头处理
  client.addRequestInterceptor({
    fulfilled: async (config) => {
      const accessStore = useAccessStore();

      config.headers.Authorization = formatToken(accessStore.accessToken);
      config.headers['Accept-Language'] = preferences.app.locale;
      return config;
    },
  });

  // 处理返回的响应数据格式
  client.addResponseInterceptor(
    defaultResponseInterceptor({
      codeField: 'code',
      dataField: 'data',
      successCode: 0,
    }),
  );

  // token过期的处理
  client.addResponseInterceptor(
    authenticateResponseInterceptor({
      client,
      doReAuthenticate,
      doRefreshToken,
      enableRefreshToken: preferences.app.enableRefreshToken,
      formatToken,
    }),
  );

  // 通用的错误处理,如果没有进入上面的错误处理逻辑，就会进入这里
  client.addResponseInterceptor(
    errorMessageResponseInterceptor((msg: string, error) => {
      // 这里可以根据业务进行定制,你可以拿到 error 内的信息进行定制化处理，根据不同的 code 做不同的提示，而不是直接使用 message.error 提示 msg
      // 当前mock接口返回的错误字段是 error 或者 message
      const responseData = error?.response?.data ?? {};
      const errorMessage = responseData?.error ?? responseData?.message ?? '';
      // 如果没有错误信息，则会根据状态码进行提示
      message.error(errorMessage || msg);
    }),
  );

  return client;
}

export const requestClient = createRequestClient(apiURL, {
  responseReturn: 'data',
});

export const baseRequestClient = new RequestClient({ baseURL: apiURL });
