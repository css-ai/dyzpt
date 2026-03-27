<script lang="ts" setup>
// VbenFormSchema：表单字段配置项类型
import type { VbenFormSchema } from '@vben/common-ui';

// computed：计算属性；markRaw：标记为非响应式的原始对象（避免组件被代理）
import { computed, markRaw } from 'vue';

// AuthenticationLogin：登录页面通用表单容器组件
// SliderCaptcha：滑块验证码组件
// z：Zod 表单校验库（用于定义字段规则）
import { AuthenticationLogin, SliderCaptcha, z } from '@vben/common-ui';
// $t：国际化翻译函数
import { $t } from '@vben/locales';

// useAuthStore：鉴权 store，提供 authLogin 登录方法和 loginLoading 状态
import { useAuthStore } from '#/store';

defineOptions({ name: 'Login' });

const authStore = useAuthStore();

const formSchema = computed((): VbenFormSchema[] => {
  return [
    {
      component: 'VbenInput',
      componentProps: {
        placeholder: $t('authentication.usernameTip'),
      },
      fieldName: 'username',
      label: $t('authentication.username'),
      rules: z.string().min(1, { message: $t('authentication.usernameTip') }),
    },
    {
      component: 'VbenInputPassword',
      componentProps: {
        placeholder: $t('authentication.password'),
      },
      fieldName: 'password',
      label: $t('authentication.password'),
      rules: z.string().min(1, { message: $t('authentication.passwordTip') }),
    },
    {
      component: markRaw(SliderCaptcha),
      fieldName: 'captcha',
      rules: z.boolean().refine((value) => value, {
        message: $t('authentication.verifyRequiredTip'),
      }),
    },
  ];
});
</script>

<template>
  <AuthenticationLogin
    :form-schema="formSchema"
    :loading="authStore.loginLoading"
    @submit="authStore.authLogin"
  />
</template>
