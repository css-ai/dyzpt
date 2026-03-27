// BasicLayout：主框架布局（含侧边栏、顶栏、通知、用户下拉等）
const BasicLayout = () => import('./basic.vue');
// AuthPageLayout：认证页布局（登录/注册/忘记密码等页面的外层容器）
const AuthPageLayout = () => import('./auth.vue');
// BlankLayout：空白布局（无任何框架样式，用于模板预览等独立页面）
const BlankLayout = () => import('./blank.vue');

// IFrameView：内嵌 iframe 页面视图，从 @vben/layouts 按需引入
const IFrameView = () => import('@vben/layouts').then((m) => m.IFrameView);

export { AuthPageLayout, BasicLayout, BlankLayout, IFrameView };
