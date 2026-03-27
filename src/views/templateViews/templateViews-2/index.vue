<script lang="ts" setup>
import { computed } from 'vue';
import type { GeneratedTemplate } from '#/store/template';
import Navigation from '../Navigation.vue';

interface Props {
  template: GeneratedTemplate;
}

const props = defineProps<Props>();

const bodyStyle = computed(() => ({
  backgroundColor: props.template.colors.background,
  color: props.template.colors.text,
  fontFamily: props.template.fonts.body,
}));

const headerStyle = computed(() => ({
  background: `linear-gradient(to right, ${props.template.colors.primary}, ${props.template.colors.secondary})`,
  color: props.template.colors.background,
}));

const accentStyle = computed(() => ({
  color: props.template.colors.primary,
  borderColor: props.template.colors.primary,
}));
</script>

<template>
  <div class="site-wrapper" :style="bodyStyle">
    <Navigation :template="template" />
    
    <div class="header-section" :style="headerStyle">
      <div class="header-container">
        <h1>{{ template.siteName }}</h1>
        <p class="subtitle">{{ template.siteDescription || '专业企业解决方案提供商' }}</p>
      </div>
    </div>

    <div class="main-content">
      <div class="container">
        <section class="intro-section">
          <h2>欢迎</h2>
          <p>我们致力于为企业提供专业的解决方案和优质的服务。通过创新的技术和专业的团队，帮助您的企业实现数字化转型。</p>
        </section>

        <section class="services-section">
          <h2>我们的服务</h2>
          <div class="services-grid">
            <div class="service-item">
              <div class="service-number">01</div>
              <h3>咨询服务</h3>
              <p>为您的企业提供专业的战略咨询和业务指导</p>
            </div>
            <div class="service-item">
              <div class="service-number">02</div>
              <h3>技术支持</h3>
              <p>提供全面的技术支持和系统维护服务</p>
            </div>
            <div class="service-item">
              <div class="service-number">03</div>
              <h3>解决方案</h3>
              <p>定制化的企业解决方案，满足您的特定需求</p>
            </div>
            <div class="service-item">
              <div class="service-number">04</div>
              <h3>培训服务</h3>
              <p>专业的员工培训和技能提升计划</p>
            </div>
          </div>
        </section>

        <section class="stats-section">
          <div class="stat-item">
            <div class="stat-number">500+</div>
            <p>服务客户</p>
          </div>
          <div class="stat-item">
            <div class="stat-number">15+</div>
            <p>年行业经验</p>
          </div>
          <div class="stat-item">
            <div class="stat-number">98%</div>
            <p>客户满意度</p>
          </div>
          <div class="stat-item">
            <div class="stat-number">24/7</div>
            <p>技术支持</p>
          </div>
        </section>
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

.header-section {
  padding: 80px 20px;
  text-align: center;
}

.header-container h1 {
  margin: 0 0 16px 0;
  font-size: 44px;
  font-weight: bold;
}

.subtitle {
  margin: 0;
  font-size: 18px;
  opacity: 0.9;
}

.main-content {
  flex: 1;
  padding: 60px 20px;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

section {
  margin-bottom: 60px;
}

section h2 {
  margin: 0 0 30px 0;
  font-size: 32px;
  text-align: center;
}

.intro-section p {
  margin: 0;
  font-size: 16px;
  line-height: 1.8;
  text-align: center;
  max-width: 600px;
  margin: 0 auto;
}

.services-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 30px;
  margin-top: 40px;
}

.service-item {
  padding: 30px;
  border-left: 4px solid;
  border-color: v-bind('accentStyle.borderColor');
  background: rgba(0, 0, 0, 0.02);
  transition: all 0.3s ease;
}

.service-item:hover {
  transform: translateX(8px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.service-number {
  font-size: 32px;
  font-weight: bold;
  color: v-bind('accentStyle.color');
  margin-bottom: 12px;
}

.service-item h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
}

.service-item p {
  margin: 0;
  font-size: 14px;
  opacity: 0.7;
  line-height: 1.6;
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 30px;
  margin-top: 40px;
  padding: 40px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 36px;
  font-weight: bold;
  color: v-bind('accentStyle.color');
  margin-bottom: 8px;
}

.stat-item p {
  margin: 0;
  font-size: 14px;
  opacity: 0.7;
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


