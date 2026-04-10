<script lang="ts" setup>
import { computed } from 'vue';
import type { GeneratedTemplate } from '#/store/template';

interface Props {
  template: GeneratedTemplate;
}

const props = defineProps<Props>();

const navItems = computed(() =>
  props.template.navItems?.length
    ? props.template.navItems
    : [
        { name: '首页', route: 'top' },
        { name: '关于', route: 'about' },
        { name: '案例', route: 'showcase' },
      ],
);

const navStyle = computed(() => ({
  '--nav-primary': props.template.colors.primary,
  '--nav-secondary': props.template.colors.secondary,
  '--nav-bg': 'rgba(13, 11, 10, 0.82)',
  '--nav-text': '#f8efe3',
  '--nav-font': props.template.fonts.heading,
}));
</script>

<template>
  <nav :style="navStyle" class="site-nav">
    <div class="nav-container">
      <a class="nav-brand" href="#top">
        <div class="brand-copy">
          <strong>{{ template.siteName }}</strong>
        </div>
      </a>

      <ul class="nav-menu">
        <li v-for="item in navItems" :key="item.route" class="nav-item">
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
  position: sticky;
  top: 0;
  z-index: 120;
  padding: 18px 0;
  backdrop-filter: blur(18px);
  background: linear-gradient(180deg, rgba(112, 215, 255, 0.78) 0%, rgba(23, 188, 238, 0.52) 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.nav-container {
  max-width: 1320px;
  margin: 0 auto;
  padding: 0 24px;
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 24px;
}

.nav-brand {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  color: var(--nav-text);
  text-decoration: none;
}

.brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.22);
  background: radial-gradient(circle at top, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.04));
  font-size: 12px;
  letter-spacing: 0.18em;
}

.brand-copy {
  display: flex;
  flex-direction: column;
}

.brand-copy strong {
  font-family: var(--nav-font), 'Microsoft YaHei', serif;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.brand-copy small {
  margin-top: 2px;
  font-size: 11px;
  letter-spacing: 0.24em;
  color: rgba(248, 239, 227, 0.6);
}

.nav-menu {
  display: flex;
  justify-content: center;
  gap: 30px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.nav-item {
  position: relative;
}

.nav-item > a {
  position: relative;
  display: inline-flex;
  align-items: center;
  padding: 8px 0;
  color: rgba(248, 239, 227, 0.88);
  text-decoration: none;
  font-size: 14px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  transition: color 0.25s ease;
}

.nav-item > a::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: -2px;
  width: 100%;
  height: 1px;
  transform: scaleX(0);
  transform-origin: left;
  background: linear-gradient(90deg, var(--nav-secondary) 0%, rgba(255, 255, 255, 0.85) 100%);
  transition: transform 0.25s ease;
}

.nav-item:hover > a {
  color: #fffdf8;
}

.nav-item:hover > a::after {
  transform: scaleX(1);
}

.nav-submenu {
  display: none;
  position: absolute;
  top: calc(100% + 12px);
  left: -14px;
  min-width: 180px;
  margin: 0;
  padding: 10px;
  list-style: none;
  border-radius: 18px;
  background: rgba(18, 15, 12, 0.96);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.28);
}

.nav-item:hover .nav-submenu {
  display: block;
}

.nav-submenu li a {
  display: block;
  padding: 10px 12px;
  color: rgba(248, 239, 227, 0.8);
  text-decoration: none;
  border-radius: 12px;
  transition: background-color 0.2s ease;
}

.nav-submenu li a:hover {
  background: rgba(255, 255, 255, 0.06);
}

.nav-cta {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 120px;
  padding: 12px 22px;
  border-radius: 999px;
  text-decoration: none;
  background: linear-gradient(135deg, var(--nav-secondary) 0%, color-mix(in srgb, var(--nav-secondary) 70%, white 30%) 100%);
  color: #201912;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.1em;
  box-shadow: 0 14px 24px rgba(0, 0, 0, 0.22);
  transition: transform 0.25s ease;
}

.nav-cta:hover {
  transform: translateY(-2px);
}

@media (max-width: 960px) {
  .nav-container {
    grid-template-columns: 1fr;
    justify-items: center;
  }

  .nav-menu {
    flex-wrap: wrap;
    gap: 18px;
  }
}

@media (max-width: 640px) {
  .site-nav {
    padding: 14px 0;
  }

  .nav-container {
    padding: 0 16px;
    gap: 14px;
  }

  .nav-menu {
    gap: 14px;
  }

  .nav-item > a {
    font-size: 12px;
    letter-spacing: 0.08em;
  }

  .nav-cta {
    width: 100%;
  }
}
</style>
