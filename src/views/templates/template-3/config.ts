export const template3Config = {
  id: 'template-3',
  name: '创意设计风格',
  description: '适合创意行业的设计感企业门户网站模板',
  thumbnail: 'https://via.placeholder.com/300x200?text=Template+3',
  category: 'creative',
  navItems: [
    {
      name: '首页',
      route: '/home',
      icon: 'lucide:home',
      children: [],
    },
    {
      name: '作品展示',
      route: '/portfolio',
      icon: 'lucide:image',
      children: [
        {
          name: '全部作品',
          route: '/portfolio/all',
          icon: 'lucide:grid',
          children: [],
        },
        {
          name: '分类作品',
          route: '/portfolio/category',
          icon: 'lucide:filter',
          children: [],
        },
      ],
    },
    {
      name: '服务项目',
      route: '/services',
      icon: 'lucide:star',
      children: [],
    },
    {
      name: '团队介绍',
      route: '/team',
      icon: 'lucide:users',
      children: [],
    },
    {
      name: '博客',
      route: '/blog',
      icon: 'lucide:book',
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
    primary: '#ff6b6b',
    secondary: '#4ecdc4',
    background: '#ffffff',
    text: '#2d3436',
  },
  fonts: {
    heading: 'Trebuchet MS, sans-serif',
    body: 'Trebuchet MS, sans-serif',
  },
};

