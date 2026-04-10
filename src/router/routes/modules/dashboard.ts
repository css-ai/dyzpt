import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:layout-dashboard',
      order: -1,
      title: $t('page.dashboard.title'),
    },
    name: 'Dashboard',
    path: '/dashboard',
    children: [
      {
        name: 'Analytics',
        path: '/analytics',
        component: () => import('#/views/dashboard/analytics/index.vue'),
        meta: {
          affixTab: true,
          icon: 'lucide:area-chart',
          title: $t('page.dashboard.analytics'),
        },
      },
      {
        name: 'Workspace',
        path: '/workspace',
        component: () => import('#/views/dashboard/workspace/index.vue'),
        meta: {
          icon: 'carbon:workspace',
          title: $t('page.dashboard.workspace'),
        },
      },
      {
        name: 'RegisterKeys',
        path: '/register-keys',
        component: () => import('#/views/dashboard/register-keys/index.vue'),
        meta: {
          icon: 'lucide:key-round',
          title: '生成密钥',
          authority:['super','admin']
        },
      },
      {
        name: 'RegisterStats',
        path: '/register-stats',
        component: () => import('#/views/dashboard/register-stats/index.vue'),
        meta: {
          icon: 'lucide:chart-column-big',
          title: '注册统计',
          authority:['super','admin']
        },
      },
      {
        name: 'Recharge',
        path: '/recharge',
        component: () => import('#/views/dashboard/recharge/index.vue'),
        meta: {
          icon: 'lucide:coins',
          title: '充值中心',
          authority: ['user'],
        },
      },
      {
        name: 'PlanManage',
        path: '/plan-manage',
        component: () => import('#/views/dashboard/plan-manage/index.vue'),
        meta: {
          icon: 'lucide:wallet-cards',
          title: '套餐管理',
          authority: ['super', 'admin'],
        },
      },
      {
        name: 'Trash',
        path: '/trash',
        component: () => import('#/views/dashboard/trash/index.vue'),
        meta: {
          icon: 'lucide:trash-2',
          title: '回收站',
          authority: ['super', 'admin'],
        },
      },
      {
        name:'WebEditor',
        path:'/webeditor',
        component:()=>import('#/views/dashboard/WebEditor/index.vue'),
        meta:{
          icon:'lucide:panels-top-left',
          title:'网页编辑',
          authority:['super','admin','user']
        }
      }
    ],
  },
];




export default routes;
