import type { PaletteCategory, PreviewDevice } from './types'

export const STORAGE_KEY = 'enterprise-editor-schema'
export const HISTORY_MAX = 50
export const AUTO_SAVE_DELAY = 1000

export const previewDevices: Array<{ label: string; value: PreviewDevice; width: number | null }> = [
  { label: 'PC', value: 'desktop', width: null },
  { label: '平板', value: 'tablet', width: 834 },
  { label: '手机', value: 'mobile', width: 390 },
]

export const paletteCategories: PaletteCategory[] = [
  {
    name: '布局组件',
    icon: '📐',
    items: [
      {
        type: 'section',
        name: '区块',
        icon: '📦',
        description: '带标题的内容区块',
        defaultProps: {
          title: '区块标题',
          subtitle: '这是区块描述文字',
          padding: { top: 48, right: 24, bottom: 48, left: 24 },
          background: '#ffffff',
          maxWidth: '1200px',
          layout: 'flex',
        },
        defaultChildren: [
          {
            id: 'default-text-1',
            type: 'text',
            name: '文本',
            props: { text: '在这里编辑你的内容...', align: 'center', fontSize: 16, color: '#333333' },
          },
        ],
      },
      {
        type: 'container',
        name: '容器',
        icon: '🗃️',
        description: '可嵌套的容器组件',
        defaultProps: {
          padding: { top: 16, right: 16, bottom: 16, left: 16 },
          background: '#f8f9fa',
          layout: 'flex',
          gap: 16,
        },
      },
    ],
  },
  {
    name: '基础组件',
    icon: '🎨',
    items: [
      {
        type: 'text',
        name: '文本',
        icon: '📝',
        description: '可编辑的文本块',
        defaultProps: { text: '双击编辑文本', align: 'left', fontSize: 16, color: '#333333' },
      },
      {
        type: 'image',
        name: '图片',
        icon: '🖼️',
        description: '图片展示',
        defaultProps: { src: 'https://picsum.photos/300/200', alt: '示例图片', width: '100%', objectFit: 'cover' },
      },
      {
        type: 'button',
        name: '按钮',
        icon: '🔘',
        description: '可配置的按钮',
        defaultProps: { text: '按钮', type: 'primary', size: 'medium' },
      },
    ],
  },
  {
    name: '业务组件',
    icon: '⚙️',
    items: [
      {
        type: 'nav',
        name: '导航栏',
        icon: '🧭',
        description: '响应式导航菜单',
        defaultProps: {
          items: [
            { label: '首页', href: '/' },
            { label: '产品', href: '/products' },
            { label: '关于', href: '/about' },
            { label: '联系', href: '/contact' },
          ],
          align: 'center',
          theme: 'light',
        },
      },
      {
        type: 'hero',
        name: 'Hero区块',
        icon: '🌟',
        description: '大标题宣传区',
        defaultProps: {
          title: '欢迎使用企业级编辑器',
          subtitle: '快速构建专业级页面',
          buttonText: '开始使用',
          overlay: true,
        },
      },
      {
        type: 'features',
        name: '特性列表',
        icon: '✨',
        description: '展示产品特性',
        defaultProps: {
          title: '核心特性',
          columns: 3,
          items: [
            { title: '特性一', description: '描述特性的具体内容' },
            { title: '特性二', description: '描述特性的具体内容' },
            { title: '特性三', description: '描述特性的具体内容' },
          ],
        },
      },
      {
        type: 'footer',
        name: '页脚',
        icon: '📋',
        description: '网站底部信息',
        defaultProps: {
          copyright: '© 2024 企业级编辑器. All rights reserved.',
          links: [
            { label: '关于我们', href: '/about' },
            { label: '隐私政策', href: '/privacy' },
            { label: '服务条款', href: '/terms' },
          ],
          theme: 'light',
        },
      },
    ],
  },
]

