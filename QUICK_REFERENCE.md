# 企业门户网站模板系统 - 快速参考指南

## 🚀 快速开始

### 访问后台管理系统
```
http://localhost:5173/dashboard/analytics    # 模板库
http://localhost:5173/dashboard/workspace    # 模板管理
```

### 访问生成的网站
```
http://localhost:5173/site/{templateId}      # 企业网站展示
```

## 📋 核心功能

### 1️⃣ 模板库展示 (analytics)
- 浏览所有可用模板
- 预览模板效果
- 生成新模板

### 2️⃣ 模板管理 (workspace)
- 查看已生成模板
- 编辑模板信息
- 修改样式配置
- 管理导航菜单
- 访问网站链接

### 3️⃣ 网站展示 (/site/:id)
- 独立企业网站页面
- 无需登录访问
- 完整的网站功能

## 📁 文件结构速查

```
src/
├── views/
│   ├── templates/              # 模板配置
│   │   ├── template-1/config.ts
│   │   ├── template-2/config.ts
│   │   ├── template-3/config.ts
│   │   └── TemplatePreview.vue
│   ├── dashboard/
│   │   ├── analytics/index.vue # 模板库
│   │   └── workspace/index.vue # 模板管理
│   └── templateViews/          # 网站展示
│       ├── index.vue
│       ├── Navigation.vue
│       ├── templateViews-1/index.vue
│       ├── templateViews-2/index.vue
│       └── templateViews-3/index.vue
├── store/
│   └── template.ts             # 状态管理
└── router/routes/modules/
    └── template-view.ts        # 路由配置
```

## 🎨 三种网站模板

| 模板 | 配色 | 特点 | 适用 |
|------|------|------|------|
| Template 1 | 蓝色系 | 现代科技 | 科技公司 |
| Template 2 | 黑金系 | 商务优雅 | 传统企业 |
| Template 3 | 红青系 | 创意设计 | 设计公司 |

## 🔄 工作流程

```
1. 访问 /dashboard/analytics
   ↓
2. 选择模板 → 预览 → 生成
   ↓
3. 填写信息（名称、描述、路径）
   ↓
4. 访问 /dashboard/workspace
   ↓
5. 查看、编辑、管理模板
   ↓
6. 点击"访问网站"或访问 /site/{id}
   ↓
7. 查看企业门户网站
```

## 💾 数据存储

- **存储位置**: localStorage
- **存储键**: `vben-generated-templates`
- **自动保存**: 每次操作后自动保存
- **加载时机**: 应用启动时自动加载

## 🛠️ 常用操作

### 生成模板
1. 选择模板
2. 点击"生成模板"
3. 填写：
   - 网站名称 ✓ 必填
   - 网站描述 ○ 可选
   - 网站路径 ✓ 必填 (格式: /path-name)

### 编辑模板
1. 在 workspace 选择模板
2. 点击"编辑模板"
3. 修改：
   - 网站名称/描述
   - 颜色配置
   - 导航菜单
4. 点击"保存更改"

### 访问网站
1. 在 workspace 查看模板
2. 点击"访问网站"链接
3. 或直接访问: `/site/{templateId}`

## 📝 网站路径规则

- **格式**: `/path-name`
- **必须以 `/` 开头**
- **允许字符**: 字母、数字、下划线、连字符
- **示例**: `/my-company`, `/site-001`, `/company_portal`

## 🎯 Store 方法

```typescript
// 获取所有可用模板
templateStore.getAvailableTemplates()

// 获取单个模板
templateStore.getTemplate(id)

// 生成新模板
templateStore.generateTemplate(templateId, siteName, siteDescription, sitePath)

// 获取所有已生成模板
templateStore.getGeneratedTemplates()

// 获取单个已生成模板
templateStore.getGeneratedTemplate(id)

// 更新模板
templateStore.updateGeneratedTemplate(id, updates)

// 删除模板
templateStore.deleteGeneratedTemplate(id)
```

## 🔗 路由配置

```typescript
// 后台管理路由
/dashboard/analytics              # 模板库
/dashboard/workspace              # 模板管理

// 网站展示路由
/site/:id                         # 企业网站
```

## 📊 数据模型

### GeneratedTemplate
```typescript
{
  id: string;                    // 模板 ID
  templateId: string;            // 源模板 ID
  templateName: string;          // 源模板名称
  siteName: string;              // 网站名称
  siteDescription: string;       // 网站描述
  sitePath: string;              // 网站路径
  navItems: NavItem[];           // 导航菜单
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
  createdAt: string;             // 创建时间
  updatedAt: string;             // 更新时间
}
```

## ⚙️ 配置修改

### 添加新模板

1. 创建模板配置文件:
```typescript
// src/views/templates/template-4/config.ts
export const template4Config = {
  id: 'template-4',
  name: '新模板名称',
  // ... 其他配置
};
```

2. 更新 Store:
```typescript
// src/store/template.ts
import { template4Config } from '#/views/templates/template-4/config';

const availableTemplates = ref<TemplateConfig[]>([
  template1Config,
  template2Config,
  template3Config,
  template4Config,  // 添加新模板
]);
```

3. 创建网站页面:
```typescript
// src/views/templateViews/templateViews-4/index.vue
// 复制 templateViews-1/index.vue 并修改
```

## 🐛 常见问题

### Q: 生成的模板在哪里查看？
A: 访问 `/dashboard/workspace` 或点击"访问网站"链接

### Q: 如何修改网站样式？
A: 在 workspace 选择模板，点击"编辑模板"，修改颜色配置

### Q: 网站路径有什么限制？
A: 必须以 `/` 开头，只能包含字母、数字、下划线和连字符

### Q: 数据会保存到哪里？
A: 保存在浏览器的 localStorage 中，清除缓存会丢失数据

### Q: 如何删除模板？
A: 在 workspace 选择模板，点击"删除"按钮

## 📚 文档导航

| 文档 | 说明 |
|------|------|
| COMPLETE_PROJECT_SUMMARY.md | 完整项目总结 |
| TEMPLATE_SYSTEM_SUMMARY.md | 系统实现总结 |
| TEMPLATE_VIEWS_UPDATE.md | 网站展示功能 |
| PROJECT_CHECKLIST.md | 项目清单 |
| src/views/templates/README.md | 模板系统文档 |
| src/views/templates/QUICKSTART.md | 快速开始指南 |

## 🎓 学习资源

- [Vue 3 官方文档](https://vuejs.org/)
- [Pinia 官方文档](https://pinia.vuejs.org/)
- [Vue Router 官方文档](https://router.vuejs.org/)
- [TypeScript 官方文档](https://www.typescriptlang.org/)

## 💡 最佳实践

1. **命名规范**
   - 模板 ID: `template-{number}`
   - 网站路径: `/kebab-case`
   - 组件名: PascalCase

2. **代码组织**
   - 配置文件放在 `config.ts`
   - 组件放在 `index.vue`
   - 样式使用 Scoped CSS

3. **数据管理**
   - 使用 Pinia Store 管理状态
   - 使用 localStorage 持久化数据
   - 定期备份重要数据

4. **性能优化**
   - 使用组件懒加载
   - 避免不必要的重新渲染
   - 优化样式和脚本

## 🚀 部署建议

1. **开发环境**
   ```bash
   npm run dev
   ```

2. **生产构建**
   ```bash
   npm run build
   ```

3. **预览构建**
   ```bash
   npm run preview
   ```

## 📞 支持

如有问题或建议，请参考项目文档或联系开发团队。

---

**快速参考版本**: 1.0

**最后更新**: 2024年

**项目状态**: ✅ 完成





