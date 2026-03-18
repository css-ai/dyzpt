# 页面管理系统使用说明

## 功能概述

这是一个基于 Vben Admin 5.6.0 的页面管理系统，包含以下三个核心功能：

### 1. 生成页面（模板页面）
- 路径：`/page-manager/template`
- 功能：基于默认模板快速生成新页面
- 操作：填写页面标题和路由，点击"生成页面"按钮

### 2. 编辑页面（JSON 编辑）
- 路径：`/page-manager/editor?id={页面ID}`
- 功能：通过 JSON 配置修改页面结构
- 支持实时预览导航结构

### 3. 查看页面（预览）
- 路径：`/page-manager/preview/{页面ID}`
- 功能：预览生成的页面效果
- 显示页面信息、导航结构和 JSON 配置

### 4. 生成的页面
- 路径：`/page-manager/generated/{页面ID}`
- 功能：实际渲染的页面，包含完整的导航和内容

## JSON 配置格式示例

```json
{
  "id": "1234567890",
  "title": "我的网站",
  "body": {
    "route": "/my-site",
    "children": [
      {
        "name": "首页",
        "route": "/index"
      },
      {
        "name": "产品",
        "route": "/products",
        "children": [
          {
            "name": "产品1",
            "route": "/products/1"
          },
          {
            "name": "产品2",
            "route": "/products/2"
          },
          {
            "name": "产品3",
            "route": "/products/3"
          }
        ]
      },
      {
        "name": "关于",
        "route": "/about"
      }
    ]
  },
  "createdAt": "2024-03-05T10:00:00.000Z",
  "updatedAt": "2024-03-05T10:00:00.000Z"
}
```

## 数据存储

- 所有页面配置存储在浏览器的 localStorage 中
- 键名：`vben-page-configs`
- 数据会在页面刷新后保持

## 快速开始

1. 访问 `/page-manager/template` 生成页面
2. 点击"编辑"按钮修改 JSON 配置
3. 点击"查看"按钮预览页面效果
4. 点击"打开页面"查看实际渲染的页面








