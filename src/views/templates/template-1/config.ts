export const template1Config = {
  id: 'template-1',
  name: '现代科技风格',
  description: '适合科技公司的现代化企业门户网站模板',
  thumbnail: 'https://via.placeholder.com/300x200?text=Template+1',
  category: 'tech',
  navItems: [
    {
      name: '首页',
      route: '/home',
      icon: 'lucide:home',
      children: []
    },
    {
      name: '产品中心',
      route: '/products',
      icon: 'lucide:package',
      children: [
        {
          name: '产品列表',
          route: '/products/list',
          icon: 'lucide:list',
          children: [],
        },
        {
          name: '产品详情',
          route: '/products/detail',
          icon: 'lucide:info',
          children: [],
        },
      ],
    },
    {
      name: '解决方案',
      route: '/solutions',
      icon: 'lucide:lightbulb',
      children: [],
    },
    {
      name: '关于我们',
      route: '/about',
      icon: 'lucide:users',
      children: [],
    },
    {
      name: '联系我们',
      route: '/contact',
      icon: 'lucide:mail',
      children: [],
    },
  ],
  colors: {
    primary: '#0066cc',
    secondary: '#00d4ff',
    background: '#ffffff',
    text: '#333333',
  },
  fonts: {
    heading: 'Arial, sans-serif',
    body: 'Arial, sans-serif',
  },
};

