import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/site/:path',
    name: 'TemplateView',
    component: () => import('#/views/templateViews/index.vue'),
    meta: {
      title: '企业网站',
      layout: 'blank',
      ignoreAccess: true,
      requiresAuth: false,
    },
  },
];

export default routes;

