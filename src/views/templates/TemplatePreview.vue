<script lang="ts" setup>
import { computed } from 'vue';
import type { TemplateConfig } from '#/store/template';

interface Props {
  template: TemplateConfig;
}

const props = defineProps<Props>();

const navStyle = computed(() => ({
  backgroundColor: props.template.colors.primary,
  color: props.template.colors.background,
  fontFamily: props.template.fonts.heading,
}));

const bodyStyle = computed(() => ({
  backgroundColor: props.template.colors.background,
  color: props.template.colors.text,
  fontFamily: props.template.fonts.body,
}));
</script>

<template>
  <div class="template-preview">
    <!-- 导航栏 -->
    <nav :style="navStyle" class="preview-nav">
      <div class="nav-container">
        <div class="nav-logo">{{ template.name }}</div>
        <ul class="nav-menu">
          <li v-for="item in template.navItems" :key="item.route" class="nav-item">
            <a :href="`#${item.route}`">{{ item.name }}</a>
            <ul v-if="item.children?.length" class="nav-submenu">
              <li v-for="child in item.children" :key="child.route">
                <a :href="`#${child.route}`">{{ child.name }}</a>
              </li>
            </ul>
          </li>
        </ul>
      </div>
    </nav>

    <!-- 主体内容 -->
    <div :style="bodyStyle" class="preview-body">
      <div class="body-container">
        <h1>{{ template.name }}</h1>
        <p>{{ template.description }}</p>
        <div class="color-palette">
          <div class="color-item">
            <div class="color-box" :style="{ backgroundColor: template.colors.primary }"></div>
            <span>主色: {{ template.colors.primary }}</span>
          </div>
          <div class="color-item">
            <div class="color-box" :style="{ backgroundColor: template.colors.secondary }"></div>
            <span>辅色: {{ template.colors.secondary }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.template-preview {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  background: white;
}

.preview-nav {
  padding: 16px 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-logo {
  font-size: 18px;
  font-weight: bold;
}

.nav-menu {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
  gap: 30px;
}

.nav-item {
  position: relative;
}

.nav-item > a {
  color: inherit;
  text-decoration: none;
  font-weight: 500;
  transition: opacity 0.3s;
}

.nav-item > a:hover {
  opacity: 0.8;
}

.nav-submenu {
  display: none;
  position: absolute;
  top: 100%;
  left: 0;
  background: rgba(0, 0, 0, 0.1);
  list-style: none;
  margin: 8px 0 0 0;
  padding: 8px 0;
  border-radius: 4px;
  min-width: 150px;
}

.nav-item:hover .nav-submenu {
  display: block;
}

.nav-submenu li {
  padding: 8px 16px;
}

.nav-submenu a {
  color: inherit;
  text-decoration: none;
  font-size: 14px;
}

.preview-body {
  padding: 60px 20px;
  min-height: 300px;
}

.body-container {
  max-width: 1200px;
  margin: 0 auto;
}

.body-container h1 {
  margin: 0 0 16px 0;
  font-size: 32px;
}

.body-container p {
  margin: 0 0 32px 0;
  font-size: 16px;
  opacity: 0.8;
}

.color-palette {
  display: flex;
  gap: 24px;
}

.color-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.color-box {
  width: 40px;
  height: 40px;
  border-radius: 4px;
  border: 1px solid #ddd;
}
</style>


