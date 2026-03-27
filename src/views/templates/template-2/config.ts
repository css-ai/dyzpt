export const template2Config = {
  id: 'template-2',
  name: '商务优雅风格',
  description: '适合传统企业的商务优雅企业门户网站模板',
  thumbnail: 'https://via.placeholder.com/300x200?text=Template+2',
  category: 'business',
  navItems: [
    {
      name: '首页',
      route: '/home',
      icon: 'lucide:home',
      children: [],
    },
    {
      name: '公司简介',
      route: '/about',
      icon: 'lucide:building-2',
      children: [
        {
          name: '公司概况',
          route: '/about/overview',
          icon: 'lucide:info',
          children: [],
        },
        {
          name: '企业文化',
          route: '/about/culture',
          icon: 'lucide:heart',
          children: [],
        },
      ],
    },
    {
      name: '业务范围',
      route: '/business',
      icon: 'lucide:briefcase',
      children: [],
    },
    {
      name: '新闻中心',
      route: '/news',
      icon: 'lucide:newspaper',
      children: [],
    },
    {
      name: '人才招聘',
      route: '/careers',
      icon: 'lucide:users',
      children: [],
    },
    {
      name: '联系我们',
      route: '/contact',
      icon: 'lucide:phone',
      children: [],
    },
  ],
  colors: {
    primary: '#1a1a1a',
    secondary: '#d4af37',
    background: '#f5f5f5',
    text: '#333333',
  },
  fonts: {
    heading: 'Georgia, serif',
    body: 'Georgia, serif',
  },
};


