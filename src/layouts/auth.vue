<script lang="ts" setup>
// computed：计算属性，用于从偏好配置中响应式获取应用名和 logo
import { computed } from 'vue';

// AuthPageLayout：认证页通用布局容器（@vben/layouts 提供，含 logo、标题、描述等插槽）
import { AuthPageLayout } from '@vben/layouts';
// preferences：全局偏好配置，读取应用名称和 logo 路径
import { preferences } from '@vben/preferences';

// $t：国际化翻译函数，用于页面标题和描述的多语言支持
import { $t } from '#/locales';

const appName = computed(() => preferences.app.name);
const logo = computed(() => preferences.logo.source);
const logoDark = computed(() => preferences.logo.sourceDark);
</script>

<template>
  <AuthPageLayout
    :app-name="appName"
    :logo="logo"
    :logo-dark="logoDark"
    :page-description="$t('authentication.pageDesc')"
    :page-title="$t('authentication.pageTitle')"
  >
    <!-- 自定义工具栏 -->
    <!-- <template #toolbar></template> -->
  </AuthPageLayout>
</template>
