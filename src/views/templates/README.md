# 企业门户网站模板管理系统

## 系统概述

这是一个完整的企业门户网站模板管理系统，集成在 Vben Admin 5.6.0 后台系统中。用户可以浏览模板、预览效果、生成模板，以及管理和编辑已生成的模板。

## 项目结构

```
src/
├── views/
│   ├── templates/                    # 模板库文件夹
│   │   ├── template-1/              # 现代科技风格模板
│   │   │   └── config.ts            # 模板配置
│   │   ├── template-2/              # 商务优雅风格模板
│   │   │   └── config.ts            # 模板配置
│   │   ├── template-3/              # 创意设计风格模板
│   │   │   └── config.ts            # 模板配置
│   │   ├── TemplatePreview.vue      # 模板预览组件
│   │   └── index.ts                 # 模板索引
│   ├── dashboard/
│   │   ├── analytics/
│   │   │   └── index.vue            # 模板展示、预览、生成页面
│   │   └── workspace/
│   │       └── index.vue            # 模板管理和编辑页面
├── store/
│   ├── template.ts                  # 模板管理 Store (Pinia)
│   └── page-config.ts               # 页面配置 Store
```

## 核心功能

### 1. 模板展示与预览 (analytics 页面)

**路径**: `/dashboard/analytics`

**功能**:
- 展示所有可用的企业门户网站模板
- 支持模板卡片选择
- 实时预览模板效果（包括导航栏、配色方案等）
- 生成新模板

**主要特性**:
- 响应式网格布局
- 模板卡片悬停效果
- 模态框预览
- 表单生成模板

### 2. 模板管理与编辑 (workspace 页面)

**路径**: `/dashboard/workspace`

**功能**:
- 查看所有已生成的模板列表
- 编辑模板基本信息（网站名称、描述）
- 修改模板样式（颜色配置）
- 管理导航菜单项
- 删除模板

**主要特性**:
- 左侧模板列表，右侧编辑面板
- 颜色选择器
- 导航菜单编辑器
- 本地存储持久化

## 数据模型

### TemplateConfig (模板配置)

```typescript
interface TemplateConfig {
  id: string;                    // 模板唯一标识
  name: string;                  // 模板名称
  description: string;           // 模板描述
  thumbnail: string;             // 模板缩略图 URL
  category: string;              // 模板分类 (tech, business, creative)
  navItems: NavItem[];           // 导航菜单项
  colors: {
    primary: string;             // 主色
    secondary: string;           // 辅色
    background: string;          // 背景色
    text: string;                // 文字色
  };
  fonts: {
    heading: string;             // 标题字体
    body: string;                // 正文字体
  };
}
```

### GeneratedTemplate (已生成的模板)

```typescript
interface GeneratedTemplate {
  id: string;                    // 生成的模板唯一标识
  templateId: string;            // 源模板 ID
  templateName: string;          // 源模板名称
  siteName: string;              // 网站名称
  siteDescription: string;       // 网站描述
  navItems: NavItem[];           // 导航菜单项
  colors: TemplateConfig['colors'];
  fonts: TemplateConfig['fonts'];
  createdAt: string;             // 创建时间
  updatedAt: string;             // 更新时间
}
```

### NavItem (导航菜单项)

```typescript
interface NavItem {
  name: string;                  // 菜单项名称
  route: string;                 // 路由路径
  icon?: string;                 // 图标 (可选)
  children?: NavItem[];          // 子菜单项 (可选)
}
```

## Store 使用

### useTemplateStore

```typescript
import { useTemplateStore } from '@/store/template';

const templateStore = useTemplateStore();

// 获取所有可用模板
const templates = templateStore.getAvailableTemplates();

// 获取单个模板
const template = templateStore.getTemplate('template-1');

// 生成新模板
const generated = templateStore.generateTemplate(
  'template-1',
  '我的企业网站',
  '这是一个企业门户网站'
);

// 获取所有已生成的模板
const generatedTemplates = templateStore.getGeneratedTemplates();

// 获取单个已生成的模板
const generated = templateStore.getGeneratedTemplate('generated-123');

// 更新已生成的模板
templateStore.updateGeneratedTemplate('generated-123', {
  siteName: '新的网站名称',
  colors: { /* ... */ }
});

// 删除已生成的模板
templateStore.deleteGeneratedTemplate('generated-123');
```

## 添加新模板

### 步骤 1: 创建模板配置文件

在 `src/views/templates/template-X/config.ts` 中创建新模板：

```typescript
export const templateXConfig = {
  id: 'template-x',
  name: '新模板名称',
  description: '模板描述',
  thumbnail: 'https://via.placeholder.com/300x200?text=Template+X',
  category: 'category-name',
  navItems: [
    {
      name: '首页',
      route: '/home',
      icon: 'lucide:home',
      children: [],
    },
    // ... 更多菜单项
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
```

### 步骤 2: 更新模板索引

在 `src/views/templates/index.ts` 中添加导出：

```typescript
export { templateXConfig } from './template-x/config';
```

### 步骤 3: 更新 Store

在 `src/store/template.ts` 中导入并添加到 `availableTemplates`：

```typescript
import { templateXConfig } from '@/views/templates/template-x/config';

const availableTemplates = ref<TemplateConfig[]>([
  template1Config,
  template2Config,
  template3Config,
  templateXConfig,  // 添加新模板
]);
```

## 本地存储

系统使用浏览器的 `localStorage` 来持久化已生成的模板数据：

- **存储键**: `vben-generated-templates`
- **存储格式**: JSON 数组
- **自动保存**: 每次修改、生成或删除模板时自动保存

## 样式特点

- **现代化设计**: 使用 Ant Design 风格的配色和组件
- **响应式布局**: 适配各种屏幕尺寸
- **交互反馈**: 按钮悬停、选中状态等视觉反馈
- **模态框**: 用于预览和编辑操作
- **颜色选择器**: 原生 HTML5 颜色输入

## 扩展建议

1. **后端集成**: 将本地存储替换为后端 API 调用
2. **模板预设**: 添加更多预设模板
3. **导出功能**: 支持导出生成的模板为 HTML/CSS
4. **版本控制**: 记录模板的修改历史
5. **权限管理**: 添加用户权限控制
6. **模板分享**: 支持模板分享和协作编辑

## 常见问题

### Q: 如何修改已生成的模板？
A: 在 workspace 页面选择要编辑的模板，点击"编辑模板"按钮，修改相关信息后点击"保存更改"。

### Q: 模板数据会保存到哪里？
A: 数据保存在浏览器的 localStorage 中，清除浏览器数据会导致数据丢失。

### Q: 如何添加新的导航菜单项？
A: 在编辑模板时，点击"+ 添加菜单项"按钮，然后填写菜单名称和路由路径。

### Q: 支持多少个模板？
A: 理论上没有限制，但受浏览器 localStorage 大小限制（通常 5-10MB）。

## 许可证

MIT



