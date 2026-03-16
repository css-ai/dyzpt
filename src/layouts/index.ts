const BasicLayout = () => import('./basic.vue');
const AuthPageLayout = () => import('./auth.vue');
const BlankLayout = () => import('./blank.vue');

const IFrameView = () => import('@vben/layouts').then((m) => m.IFrameView);

export { AuthPageLayout, BasicLayout, BlankLayout, IFrameView };
