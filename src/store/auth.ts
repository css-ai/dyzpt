// Recordable：通用键值对类型；UserInfo：用户信息类型
import type { Recordable, UserInfo } from '@vben/types';

// ref：响应式变量
import { ref } from 'vue';
// useRouter：获取路由实例，用于登录后跳转
import { useRouter } from 'vue-router';

// LOGIN_PATH：登录页路由常量
import { LOGIN_PATH } from '@vben/constants';
// preferences：全局偏好配置（默认首页、登录过期模式等）
import { preferences } from '@vben/preferences';
import {
  resetAllStores,   // 退出时重置所有 store
  useAccessStore,   // 管理 accessToken 与登录过期状态
  useUserStore,     // 存储用户信息
} from '@vben/stores';

// notification：Ant Design Vue 通知提示（登录成功弹窗）
import { notification } from 'ant-design-vue';
// defineStore：Pinia store 工厂函数
import { defineStore } from 'pinia';

// 登录、退出、获取用户信息、获取权限码的 API 接口
import { getAccessCodesApi, getUserInfoApi, loginApi, logoutApi } from '#/api';
// $t：国际化翻译函数
import { $t } from '#/locales';

export const useAuthStore = defineStore('auth', () => {
  const accessStore = useAccessStore();
  const userStore = useUserStore();
  const router = useRouter();

  const loginLoading = ref(false);

  /**
   * 异步处理登录操作
   * Asynchronously handle the login process
   * @param params 登录表单数据
   */
  async function authLogin(
    params: Recordable<any>,
    onSuccess?: () => Promise<void> | void,
  ) {
    // 异步处理用户登录操作并获取 accessToken
    let userInfo: null | UserInfo = null;
    try {
      loginLoading.value = true;
      const { accessToken } = await loginApi(params);

      // 如果成功获取到 accessToken
      if (accessToken) {
        accessStore.setAccessToken(accessToken);

        // 获取用户信息并存储到 accessStore 中
        const [fetchUserInfoResult, accessCodes] = await Promise.all([
          fetchUserInfo(),
          getAccessCodesApi(),
        ]);

        userInfo = fetchUserInfoResult;

        userStore.setUserInfo(userInfo);
        accessStore.setAccessCodes(accessCodes);

        if (accessStore.loginExpired) {
          accessStore.setLoginExpired(false);
        } else {
          onSuccess
            ? await onSuccess?.()
            : await router.push(
                userInfo.homePath || preferences.app.defaultHomePath,
              );
        }

        if (userInfo?.realName) {
          notification.success({
            description: `${$t('authentication.loginSuccessDesc')}:${userInfo?.realName}`,
            duration: 3,
            message: $t('authentication.loginSuccess'),
          });
        }
      }
    } finally {
      loginLoading.value = false;
    }

    return {
      userInfo,
    };
  }

  async function logout(redirect: boolean = true) {
    try {
      await logoutApi();
    } catch {
      // 不做任何处理
    }
    resetAllStores();
    accessStore.setLoginExpired(false);

    // 回登录页带上当前路由地址
    await router.replace({
      path: LOGIN_PATH,
      query: redirect
        ? {
            redirect: encodeURIComponent(router.currentRoute.value.fullPath),
          }
        : {},
    });
  }

  async function fetchUserInfo() {
    let userInfo: null | UserInfo = null;
    userInfo = await getUserInfoApi();
    userStore.setUserInfo(userInfo);
    return userInfo;
  }

  function $reset() {
    loginLoading.value = false;
  }

  return {
    $reset,
    authLogin,
    fetchUserInfo,
    loginLoading,
    logout,
  };
});
