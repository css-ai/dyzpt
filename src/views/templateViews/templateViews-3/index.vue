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

const bannerStyle = computed(() => ({
  background: `linear-gradient(45deg, ${props.template.colors.primary}, ${props.template.colors.secondary})`,
  color: props.template.colors.background,
}));

const accentStyle = computed(() => ({
  color: props.template.colors.primary,
  backgroundColor: props.template.colors.secondary,
}));
</script>

<template>
  <div class="site-wrapper" :style="bodyStyle">
    <Navigation :template="template" />
    
    <div class="banner-section" :style="bannerStyle">
      <div class="banner-content">
        <h1>{{ template.siteName }}</h1>
        <p>{{ template.siteDescription || '创意设计，专业服务' }}</p>
      </div>
    </div>

    <div class="main-content">
      <div class="container">
        <section class="about-section">
          <h2>关于我们</h2>
          <div class="about-grid">
            <div class="about-item">
              <div class="about-icon">🎯</div>
              <h3>我们的使命</h3>
              <p>通过创意和创新，为客户创造价值，推动行业发展</p>
            </div>
            <div class="about-item">
              <div class="about-icon">💡</div>
              <h3>我们的愿景</h3>
              <p>成为行业领先的创意设计和解决方案提供商</p>
            </div>
            <div class="about-item">
              <div class="about-icon">🤝</div>
              <h3>我们的价值</h3>
              <p>诚信、创新、卓越、合作是我们的核心价值观</p>
            </div>
          </div>
        </section>

        <section class="portfolio-section">
          <h2>作品展示</h2>
          <div class="portfolio-grid">
            <div v-for="i in 6" :key="i" class="portfolio-item">
              <div class="portfolio-image">
                <div class="placeholder">作品 {{ i }}</div>
              </div>
              <h3>项目名称 {{ i }}</h3>
              <p>项目描述和相关信息</p>
            </div>
          </div>
        </section>

        <section class="team-section">
          <h2>我们的团队</h2>
          <p class="section-desc">由行业专家和创意人才组成的专业团队</p>
          <div class="team-grid">
            <div v-for="i in 4" :key="i" class="team-member">
              <div class="member-avatar">{{ String.fromCharCode(64 + i) }}</div>
              <h3>团队成员 {{ i }}</h3>
              <p class="member-role">职位</p>
            </div>
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

.banner-section {
  padding: 100px 20px;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.banner-content h1 {
  margin: 0 0 16px 0;
  font-size: 48px;
  font-weight: bold;
}

.banner-content p {
  margin: 0;
  font-size: 20px;
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
  margin-bottom: 80px;
}

section h2 {
  margin: 0 0 40px 0;
  font-size: 36px;
  text-align: center;
}

.section-desc {
  text-align: center;
  font-size: 16px;
  opacity: 0.7;
  margin: -30px 0 30px 0;
}

.about-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 30px;
}

.about-item {
  text-align: center;
  padding: 30px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.02);
  transition: all 0.3s ease;
}

.about-item:hover {
  transform: translateY(-8px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.about-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.about-item h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
}

.about-item p {
  margin: 0;
  font-size: 14px;
  opacity: 0.7;
  line-height: 1.6;
}

.portfolio-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.portfolio-item {
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
}

.portfolio-item:hover {
  transform: scale(1.02);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.portfolio-image {
  width: 100%;
  height: 200px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  font-weight: bold;
}

.placeholder {
  text-align: center;
}

.portfolio-item h3 {
  margin: 16px 0 8px 0;
  font-size: 16px;
  padding: 0 16px;
}

.portfolio-item p {
  margin: 0;
  font-size: 13px;
  opacity: 0.7;
  padding: 0 16px 16px 16px;
}

.team-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 30px;
}

.team-member {
  text-align: center;
  padding: 30px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.02);
}

.member-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: v-bind('accentStyle.backgroundColor');
  color: v-bind('accentStyle.color');
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: bold;
  margin: 0 auto 16px;
}

.team-member h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
}

.member-role {
  margin: 0;
  font-size: 13px;
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


