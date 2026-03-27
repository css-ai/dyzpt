<script lang="ts" setup>
import { computed } from 'vue';
import type { GeneratedTemplate } from '#/store/template';

interface Props {
  template: GeneratedTemplate;
}

const props = defineProps<Props>();

const navStyle = computed(() => ({
  backgroundColor: props.template.colors.primary,
  color: props.template.colors.background,
  fontFamily: props.template.fonts.heading,
}));
</script>

<template>
  <nav :style="navStyle" class="site-nav">
    <div class="nav-container">
      <div class="nav-logo">{{ template.siteName }}</div>
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
</template>

<style scoped>
.site-nav {
  padding: 16px 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
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
  font-size: 20px;
  font-weight: bold;
  min-width: 200px;
}

.nav-menu {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
  gap: 30px;
  flex: 1;
  justify-content: center;
}

.nav-item {
  position: relative;
}

.nav-item > a {
  color: inherit;
  text-decoration: none;
  font-weight: 500;
  transition: opacity 0.3s;
  display: block;
  padding: 8px 0;
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
</style>


