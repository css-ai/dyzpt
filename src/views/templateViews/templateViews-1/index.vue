<script lang="ts" setup>
import { computed, ref } from 'vue';
import type { GeneratedTemplate } from '#/store/template';
import Navigation from '../HomePageTemplate/Navigation.vue';

interface Props {
  template: GeneratedTemplate;
}

const props = defineProps<Props>();

const pageStyle = computed(() => ({
  '--tv-primary': props.template.colors.primary,
  '--tv-secondary': props.template.colors.secondary,
  '--tv-background': props.template.colors.background,
  '--tv-text': props.template.colors.text,
  '--tv-heading-font': props.template.fonts.heading,
  '--tv-body-font': props.template.fonts.body,
}));

const siteName = computed(() => props.template.siteName || 'Burb Studio');
const siteDescription = computed(
  () => props.template.siteDescription || '创意、品牌与企业展示并重的公开官网首页。',
);

const heroSlides = [
  {
    eyebrow: 'Creative Direction',
    title: siteName.value,
    desc: '我们把品牌表达、企业能力与公开站点的第一印象，统一在一个更可维护的 Vue 模板里。',
  },
  {
    eyebrow: 'Digital Experience',
    title: 'Build pages that feel premium',
    desc: '用更好的版式、留白和模块节奏，让模板站也能有品牌感。',
  },
  {
    eyebrow: 'Launch Ready',
    title: 'From concept to production',
    desc: '后续继续补真实数据、图片资源和二级页后，就能作为正式公开页继续演进。',
  },
];
const currentHero = ref(0);

const services = [
  { code: '01', title: 'Brand Strategy', desc: '品牌定位、叙事结构和首页信息层次设计。' },
  { code: '02', title: 'Web Development', desc: '把静态模板思路拆成项目里可维护的 Vue 页面。' },
  { code: '03', title: 'UI / UX Design', desc: '统一视觉气质、版式留白和区块层次。' },
  { code: '04', title: 'Marketing Ready', desc: '预留案例、联系和转化入口，方便上线。' },
];

const projects = computed(() => [
  { title: 'Kinetic Sandscapes', meta: '2026 · Branding', desc: '偏高级展示型首页，强调品牌识别与气质。' },
  { title: 'Hopscotch Payments', meta: '2026 · Development', desc: '更适合承载产品与解决方案说明。' },
  { title: 'Brooklyn Brewery', meta: '2026 · Photography', desc: '用大图块和卡片制造模板站观感。' },
  { title: siteName.value, meta: '2026 · Creative', desc: '当前模板已重构成项目可继续使用的 Vue 结构。' },
]);

const blogs = [
  'Ready to transform your brand into something extraordinary',
  'Your vision deserves world-class execution',
  'Do not just compete — dominate the first impression',
];

const contacts = [
  { label: 'Email', value: 'hello@yoursite.com', href: 'mailto:hello@yoursite.com' },
  { label: 'Phone', value: '+1 874 414 7890', href: 'tel:+18741467890' },
  { label: 'Address', value: '245 West 52nd Street, Apt 7B New York, NY 10019', href: '#' },
];

const handleHeroChange = (current: number) => {
  currentHero.value = current;
};
</script>

<template>
  <Navigation :template="template" />
  <div class="template-shell" :style="pageStyle">


    <section id="top" class="hero-section">
      <div class="container hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">{{ heroSlides[currentHero]?.eyebrow }}</p>
          <h1>{{ heroSlides[currentHero]?.title }}</h1>
          <p class="hero-description">{{ heroSlides[currentHero]?.desc }}</p>
          <div class="hero-actions">
            <a class="hero-link primary" href="#services">查看服务</a>
            <a class="hero-link" href="#contact">立即联系</a>
          </div>
        </div>
        <div class="hero-slider panel light-panel">
          <div class="hero-track">
            <article
              v-for="(slide, index) in heroSlides"
              :key="slide.title"
              class="hero-slide"
              :class="{ active: currentHero === index }"
            >
              <span>{{ slide.eyebrow }}</span>
              <h3>{{ slide.title }}</h3>
              <p>{{ slide.desc }}</p>
            </article>
          </div>
          <div class="hero-dots" role="tablist" aria-label="Hero slides">
            <button
              v-for="(slide, index) in heroSlides"
              :key="slide.title"
              type="button"
              class="hero-dot"
              :class="{ active: currentHero === index }"
              :aria-label="`切换到第 ${index + 1} 张幻灯片`"
              @click="handleHeroChange(index)"
            />
          </div>
        </div>
      </div>
    </section>

    <section id="about" class="section container">
      <div class="section-head">
        <p class="eyebrow">ABOUT</p>
        <h2>把参考模板的商业首页结构，拆成项目里可以继续维护的 Vue 页面</h2>
      </div>
      <div class="intro-grid">
        <div class="panel light-panel">
          <p>
            这次不是直接照搬抓包里的 HTML，而是把模板站的视觉节奏、区块结构和商业首页逻辑，重组为适合你当前项目的单文件组件。
          </p>
          <p>
            这样后面无论你替换公司名称、导航、案例、联系方式还是继续补更多版块，都能直接在现有模板系统上扩展。
          </p>
        </div>
        <div class="stack-grid">
          <div class="panel dark-panel">
            <h3>Brand Strategy</h3>
            <p>从品牌定位到首页叙事结构，统一对外表达。</p>
          </div>
          <div class="panel dark-panel">
            <h3>Web Experience</h3>
            <p>延续参考模板的高级感，同时保留项目内可维护性。</p>
          </div>
        </div>
      </div>
    </section>

    <section id="services" class="section container">
      <div class="section-head narrow">
        <p class="eyebrow">SERVICES</p>
        <h2>Where Conventional Thinking Ends</h2>
      </div>
      <div class="services-grid">
        <article v-for="item in services" :key="item.code" class="panel light-panel service-card">
          <span class="service-code">{{ item.code }}</span>
          <h3>{{ item.title }}</h3>
          <p>{{ item.desc }}</p>
        </article>
      </div>
    </section>

    <section id="projects" class="section projects-section">
      <div class="container">
        <div class="section-head narrow section-head-light">
          <p class="eyebrow">PROJECTS</p>
          <h2>Selected Works & Visual Modules</h2>
        </div>
        <div class="projects-grid">
          <article v-for="item in projects" :key="item.title" class="project-card">
            <div class="project-thumb"></div>
            <div class="project-meta">{{ item.meta }}</div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.desc }}</p>
          </article>
        </div>
      </div>
    </section>

    <section id="blog" class="section container">
      <div class="section-head narrow">
        <p class="eyebrow">BLOG</p>
        <h2>Breaking Creative Boundaries Daily</h2>
      </div>
      <div class="blog-grid">
        <article v-for="item in blogs" :key="item" class="panel light-panel blog-card">
          <div class="blog-cover"></div>
          <span>June 2026</span>
          <h3>{{ item }}</h3>
        </article>
      </div>
    </section>

    <section id="contact" class="section container">
      <div class="contact-card">
        <div>
          <p class="eyebrow">CONTACT</p>
          <h2>Let’s Make Something Remarkable Together</h2>
          <p class="contact-desc">
            当前这版已经是项目内可继续维护的 Vue 模板结构。下一步你可以继续补真实图片、更多二级页和更细的动效。
          </p>
        </div>
        <div class="contact-list">
          <a v-for="item in contacts" :key="item.label" :href="item.href" class="contact-item">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </a>
        </div>
      </div>
    </section>

    <footer class="container site-footer">
      <h3>{{ siteName }}</h3>
      <p>{{ siteDescription }}</p>
      <div class="footer-links">
        <a href="#top">Home</a>
        <a href="#about">About</a>
        <a href="#services">Services</a>
        <a href="#projects">Projects</a>
        <a href="#contact">Contact</a>
      </div>
      <div class="footer-bottom">All rights reserved — 2026 © {{ siteName }}</div>
    </footer>
  </div>
</template>

<style scoped>
.template-shell {
  min-height: 100vh;
  color: var(--tv-text);
  background: linear-gradient(180deg, #f6f2ea 0%, var(--tv-background) 22%, #f3eee6 100%);
  font-family: var(--tv-body-font), 'Microsoft YaHei', sans-serif;
}

.container {
  max-width: 1280px;
  margin: 0 auto;
}

.section {
  padding: 92px 24px;
}

.hero-section {
  padding: 48px 24px 96px;
  background: #f3eee6;
}

.hero-grid,
.intro-grid,
.contact-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, .95fr);
  gap: 28px;
  align-items: center;
}

.hero-grid {
  min-height: calc(100vh - 140px);
  gap: 56px;
}

.hero-copy {
  color: #fff6ea;
}

.eyebrow {
  margin: 0 0 14px;
  font-size: 12px;
  letter-spacing: .34em;
  text-transform: uppercase;
  color: color-mix(in srgb, var(--tv-secondary) 72%, white 28%);
}

.kicker {
  margin: 0 0 12px;
  font-size: 16px;
  color: rgba(255, 246, 234, .78);
}

.hero-copy h1,
.hero-slide h3,
.section-head h2,
.panel h3,
.project-card h3,
.blog-card h3,
.contact-card h2,
.site-footer h3 {
  font-family: var(--tv-heading-font), 'Microsoft YaHei', serif;
}

.hero-copy h1 {
  margin: 0;
  font-size: clamp(50px, 7vw, 92px);
  line-height: .95;
}

.hero-desc,
.hero-description,
.panel p,
.project-card p,
.contact-desc,
.site-footer p {
  line-height: 1.9;
}

.hero-desc {
  max-width: 620px;
  margin-top: 28px;
  color: rgba(255, 246, 234, .82);
}

.hero-actions,
.hero-dots,
.footer-links {
  display: flex;
  flex-wrap: wrap;
  gap: 16px 24px;
}

.hero-actions {
  margin-top: 34px;
}

.hero-description {
  max-width: 620px;
  margin-top: 28px;
  color: rgba(23, 18, 14, .78);
}

.hero-slider {
  padding: 28px;
}

.hero-track {
  display: grid;
  gap: 18px;
}

.hero-slide {
  padding: 26px 28px;
  border-radius: 26px;
  border: 1px solid rgba(120, 96, 69, .12);
  background: rgba(255, 255, 255, .76);
  transition: all .3s ease;
  opacity: .55;
}

.hero-slide.active {
  opacity: 1;
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(25, 18, 10, .08);
}

.hero-slide span {
  display: block;
  margin-bottom: 10px;
  font-size: 12px;
  letter-spacing: .2em;
  text-transform: uppercase;
  color: color-mix(in srgb, var(--tv-secondary) 72%, black 28%);
}

.hero-slide h3 {
  margin: 0 0 12px;
  font-size: 28px;
  line-height: 1.2;
  color: #17120e;
}

.hero-slide p {
  margin: 0;
  line-height: 1.8;
  color: rgba(23, 18, 14, .72);
}

.hero-dots {
  margin-top: 22px;
}

.hero-dot {
  width: 12px;
  height: 12px;
  border-radius: 999px;
  border: none;
  background: rgba(120, 96, 69, .24);
  cursor: pointer;
  transition: all .25s ease;
}

.hero-dot.active {
  width: 38px;
  background: var(--tv-secondary);
}

.hero-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 148px;
  padding: 14px 28px;
  border-radius: 999px;
  text-decoration: none;
  color: #17120e;
  border: 1px solid rgba(120, 96, 69, .14);
  background: rgba(255, 255, 255, .68);
}

.hero-link.primary {
  background: linear-gradient(135deg, var(--tv-secondary) 0%, color-mix(in srgb, var(--tv-secondary) 68%, white 32%) 100%);
  color: #241a12;
  border: none;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 148px;
  padding: 14px 28px;
  border-radius: 999px;
  text-decoration: none;
}

.btn-primary {
  background: linear-gradient(135deg, var(--tv-secondary) 0%, color-mix(in srgb, var(--tv-secondary) 68%, white 32%) 100%);
  color: #241a12;
}

.btn-secondary {
  border: 1px solid rgba(255, 255, 255, .22);
  background: rgba(255, 255, 255, .06);
  color: #fff6ea;
}

.glass-card,
.float-card,
.project-card,
.contact-item {
  border: 1px solid rgba(255, 255, 255, .08);
  border-radius: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 42px;
}

.stat-card {
  padding: 20px 18px;
  background: rgba(255, 255, 255, .06);
}

.stat-card strong {
  display: block;
  font-size: 34px;
  color: color-mix(in srgb, var(--tv-secondary) 72%, white 28%);
}

.stat-card span {
  display: block;
  margin-top: 12px;
  color: rgba(255, 246, 234, .72);
}

.hero-stage {
  position: relative;
  min-height: 620px;
  padding: 24px;
  background: rgba(255, 255, 255, .08);
  border-radius: 36px;
}

.stage-image,
.project-thumb,
.blog-cover {
  border-radius: 24px;
  background: linear-gradient(135deg, color-mix(in srgb, var(--tv-secondary) 78%, #fff 22%) 0%, #5d4532 48%, #231912 100%);
}

.stage-image {
  position: absolute;
  inset: 24px;
}

.float-card {
  position: absolute;
  max-width: 250px;
  padding: 20px 22px;
  background: rgba(14, 11, 9, .76);
  color: #fff7ee;
}

.float-card span,
.service-code,
.project-meta,
.blog-card span,
.contact-item span {
  display: block;
  font-size: 12px;
  letter-spacing: .18em;
  text-transform: uppercase;
}

.top-note {
  top: 38px;
  right: -28px;
}

.bottom-note {
  left: -26px;
  bottom: 44px;
}

.stage-number {
  position: absolute;
  right: 34px;
  bottom: 26px;
  font-size: 78px;
  color: rgba(255, 255, 255, .2);
}

.section-head {
  max-width: 820px;
  margin-bottom: 40px;
}

.narrow {
  max-width: 700px;
}

.section-head h2 {
  margin: 0;
  font-size: clamp(32px, 4vw, 54px);
  line-height: 1.14;
  color: #17120e;
}

.section-head-light h2 {
  color: #fff5eb;
}

.panel {
  padding: 30px;
  border-radius: 28px;
  border: 1px solid rgba(120, 96, 69, .12);
  box-shadow: 0 18px 48px rgba(25, 18, 10, .06);
}

.light-panel {
  background: rgba(255, 255, 255, .82);
}

.dark-panel {
  background: linear-gradient(180deg, rgba(32, 25, 20, .96) 0%, rgba(62, 47, 33, .96) 100%);
  color: #fff6ec;
}

.stack-grid,
.services-grid,
.projects-grid,
.blog-grid,
.contact-list {
  display: grid;
  gap: 24px;
}

.services-grid {
  grid-template-columns: repeat(4, 1fr);
}

.projects-section {
  background: linear-gradient(180deg, #17120f 0%, #241b15 100%);
}

.projects-grid {
  grid-template-columns: repeat(4, 1fr);
}

.project-card {
  padding: 22px;
  background: rgba(255, 255, 255, .05);
  color: #fff4e9;
}

.project-thumb {
  height: 220px;
}

.project-meta {
  margin-top: 18px;
  color: rgba(255, 244, 233, .62);
}

.blog-grid {
  grid-template-columns: repeat(3, 1fr);
}

.blog-cover {
  height: 180px;
  margin-bottom: 18px;
}

.contact-card {
  padding: 38px;
  border-radius: 34px;
  background: linear-gradient(135deg, rgba(18, 15, 12, .98) 0%, rgba(47, 36, 27, .96) 100%);
  color: #fff7ec;
}

.contact-card h2 {
  margin: 0;
  font-size: clamp(30px, 3.6vw, 46px);
  line-height: 1.18;
}

.contact-item {
  display: block;
  padding: 20px 22px;
  text-decoration: none;
  color: #fff7ec;
  background: rgba(255, 255, 255, .06);
}

.contact-item strong {
  font-size: 16px;
  line-height: 1.6;
}

.site-footer {
  padding: 0 24px 42px;
}

.footer-links {
  margin: 22px 0;
}

.footer-links a,
.footer-bottom {
  color: rgba(39, 32, 26, .7);
  text-decoration: none;
}

@media (max-width: 1100px) {

  .hero-grid,
  .intro-grid,
  .contact-card,
  .services-grid,
  .projects-grid,
  .blog-grid {
    grid-template-columns: 1fr 1fr;
  }

  .hero-grid,
  .intro-grid,
  .contact-card {
    grid-template-columns: 1fr;
  }

  .hero-slider {
    order: -1;
  }

  .hero-stage {
    min-height: 420px;
  }
}

@media (max-width: 768px) {
  .hero-section {
    padding: 28px 16px 70px;
  }

  .section,
  .site-footer {
    padding-left: 16px;
    padding-right: 16px;
  }

  .section {
    padding-top: 68px;
    padding-bottom: 68px;
  }

  .hero-copy h1 {
    font-size: 46px;
  }

  .stats-grid,
  .services-grid,
  .projects-grid,
  .blog-grid {
    grid-template-columns: 1fr;
  }

  .hero-stage {
    min-height: 340px;
    padding: 16px;
  }

  .stage-image {
    inset: 16px;
  }

  .top-note,
  .bottom-note {
    left: 18px;
    right: auto;
  }

  .top-note {
    top: auto;
    bottom: 96px;
  }

  .bottom-note {
    bottom: 20px;
  }

  .stage-number {
    right: 18px;
    bottom: 10px;
    font-size: 42px;
  }
}
</style>
