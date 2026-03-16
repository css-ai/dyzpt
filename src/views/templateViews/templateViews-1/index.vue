<script lang="ts" setup>
import { computed } from 'vue';
import type { GeneratedTemplate } from '#/store/template';
import Navigation from './../Navigation.vue';

interface Props {
  template: GeneratedTemplate;
}

const props = defineProps<Props>();

const bodyStyle = computed(() => ({
  backgroundColor: props.template.colors.background,
  color: props.template.colors.text,
  fontFamily: props.template.fonts.body,
}));

const heroStyle = computed(() => ({
  background: `linear-gradient(135deg, ${props.template.colors.primary} 0%, ${props.template.colors.secondary} 100%)`,
  color: props.template.colors.background,
}));

const buttonStyle = computed(() => ({
  backgroundColor: props.template.colors.secondary,
  color: props.template.colors.primary,
}));
</script>

<template>
  <div class="site-wrapper" :style="bodyStyle">
    <Navigation :template="template" />
    
    <div class="hero-section" :style="heroStyle">
      <div class="hero-container">
        <h1>{{ template.siteName }}</h1>
        <p>{{ template.siteDescription || '欢迎来到我们的企业门户网站' }}</p>
        <button class="cta-button" :style="buttonStyle">了解更多</button>
      </div>
    </div>

    <div class="content-section">
      <div class="container">
        <h2>关于我们</h2>
        <p>这是一个由模板系统生成的企业门户网站。您可以通过后台管理系统自定义网站的样式、导航菜单和内容。</p>
        
        <div class="features">
          <div class="feature-card">
            <div class="feature-icon">🎨</div>
            <h3>现代设计</h3>
            <p>采用现代化的设计风格，提供专业的视觉体验</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <h3>快速响应</h3>
            <p>响应式设计，完美适配各种设备和屏幕尺寸</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">🔧</div>
            <h3>易于定制</h3>
            <p>灵活的配置选项，轻松定制您的企业网站</p>
          </div>
        </div>
      </div>
    </div>

    <footer class="footer">
      <div class="container">
        <p>&copy; 2024 {{ template.siteName }}. 版权所有。</p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.site-wrapper {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.hero-section {
  padding: 100px 20px;
  text-align: center;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-container {
  max-width: 800px;
}

.hero-section h1 {
  margin: 0 0 20px 0;
  font-size: 48px;
  font-weight: bold;
}

.hero-section p {
  margin: 0 0 30px 0;
  font-size: 18px;
  opacity: 0.9;
}

.cta-button {
  padding: 12px 32px;
  font-size: 16px;
  font-weight: 500;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cta-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.content-section {
  padding: 60px 20px;
  flex: 1;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

.content-section h2 {
  margin: 0 0 20px 0;
  font-size: 32px;
  text-align: center;
}

.content-section > .container > p {
  margin: 0 0 40px 0;
  font-size: 16px;
  text-align: center;
  line-height: 1.6;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 30px;
  margin-top: 40px;
}

.feature-card {
  padding: 30px;
  border-radius: 8px;
  text-align: center;
  background: rgba(0, 0, 0, 0.02);
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.feature-card h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
}

.feature-card p {
  margin: 0;
  font-size: 14px;
  opacity: 0.7;
  line-height: 1.5;
}

.footer {
  background: rgba(0, 0, 0, 0.05);
  padding: 30px 20px;
  text-align: center;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.footer p {
  margin: 0;
  font-size: 14px;
  opacity: 0.7;
}
</style>


