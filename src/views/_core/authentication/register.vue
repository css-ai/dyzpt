<script lang="ts" setup>
// VbenFormSchema：表单字段配置项类型
import type { VbenFormSchema } from '@vben/common-ui';
// Recordable：通用键值对类型，用于表单提交数据
import type { Recordable } from '@vben/types';

// computed：计算属性；h：渲染函数（用于自定义协议勾选框内容）；ref：响应式变量
import { computed, h, ref } from 'vue';
// useRouter：获取路由实例，注册成功后跳转到登录页
import { useRouter } from 'vue-router';

// AuthenticationRegister：注册页面通用表单容器组件
// z：Zod 表单校验库
import { AuthenticationRegister, z } from '@vben/common-ui';
// $t：国际化翻译函数
import { $t } from '@vben/locales';

// registerApi：用户注册接口（用户名 + 密码 + 注册密钥）
import { registerApi } from '#/api';

defineOptions({ name: 'Register' });

const router = useRouter();
const loading = ref(false);

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
        passwordStrength: true,
        placeholder: $t('authentication.password'),
      },
      fieldName: 'password',
      label: $t('authentication.password'),
      renderComponentContent() {
        return {
          strengthText: () => $t('authentication.passwordStrength'),
        };
      },
      rules: z.string().min(1, { message: $t('authentication.passwordTip') }),
    },
    {
      component: 'VbenInputPassword',
      componentProps: {
        placeholder: $t('authentication.confirmPassword'),
      },
      dependencies: {
        rules(values) {
          const { password } = values;
          return z
            .string({ required_error: $t('authentication.passwordTip') })
            .min(1, { message: $t('authentication.passwordTip') })
            .refine((value) => value === password, {
              message: $t('authentication.confirmPasswordTip'),
            });
        },
        triggerFields: ['password'],
      },
      fieldName: 'confirmPassword',
      label: $t('authentication.confirmPassword'),
    },
    {
      component: 'VbenInput',
      componentProps: {
        placeholder: '请输入管理员发放的密钥',
      },
      fieldName: 'register_key',
      label: '密钥',
      rules: z.string().min(1, { message: '请输入密钥' }),
    },
    {
      component: 'VbenCheckbox',
      fieldName: 'agreePolicy',
      renderComponentContent: () => ({
        default: () =>
          h('span', [
            $t('authentication.agree'),
            h(
              'a',
              {
                class: 'vben-link ml-1 ',
                href: '',
              },
              `${$t('authentication.privacyPolicy')} & ${$t('authentication.terms')}`,
            ),
          ]),
      }),
      rules: z.boolean().refine((value) => !!value, {
        message: $t('authentication.agreeTip'),
      }),
    },
  ];
});

async function handleSubmit(value: Recordable<any>) {
  loading.value = true;
  try {
    await registerApi({
      username: String(value.username || '').trim(),
      password: String(value.password || ''),
      register_key: String(value.register_key || '').trim(),
    });
    await router.push('/auth/login');
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <AuthenticationRegister
    :form-schema="formSchema"
    :loading="loading"
    @submit="handleSubmit"
  />
</template>
