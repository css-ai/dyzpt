# 企业门户网站模板管理系统

基于 **Vben Admin 5.6.0** 构建的企业门户网站模板管理后台，支持模板选择、生成、编辑、发布及用户权限管理，配套 FastAPI 后端服务。

---

## 目录

- [项目概述](#项目概述)
- [技术栈](#技术栈)
- [功能模块](#功能模块)
- [目录结构](#目录结构)
- [快速启动](#快速启动)
- [账号体系](#账号体系)
- [套餐与充值](#套餐与充值)
- [API 接口说明](#api-接口说明)
- [数据模型](#数据模型)
- [三套内置模板](#三套内置模板)
- [权限控制](#权限控制)
- [回收站机制](#回收站机制)
- [注意事项](#注意事项)
- [浏览器兼容性](#浏览器兼容性)

---

## 项目概述

本系统为企业提供一套完整的门户网站生成与管理解决方案：

- 管理员在后台选择模板、配置域名后一键生成企业门户网站
- 支持三种风格的内置模板（科技、商务、创意）
- 提供完整的用户注册、密钥管理、配额控制体系
- 普通用户可通过充值中心选择套餐，管理员可直接为用户调整套餐
- 所有删除操作均进入回收站，支持随时恢复
- 后端使用 SQLite + FastAPI，零依赖部署

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | Vue 3 + TypeScript + Composition API |
| 状态管理 | Pinia |
| UI 组件库 | Ant Design Vue |
| 路由 | Vue Router 4 |
| 构建工具 | Vite |
| 后端框架 | FastAPI (Python 3.11+) |
| 数据库 | SQLite 3 |
| 密码加密 | PBKDF2-SHA256 (260000 次迭代) |
| 身份认证 | JWT HS256（自实现，无第三方依赖）|
| 跨域处理 | FastAPI CORSMiddleware |

---

## 功能模块

### 1. 模板库（analytics）
- 展示三套内置企业门户模板，支持预览
- 选择模板后填写站点名称、描述、域名，一键生成站点页面
- 普通用户受页面配额限制，超出时给出明确提示

### 2. 模板管理工作区（workspace）
- 查看当前账号名下所有已生成的站点页面
- 编辑站点名称、描述、配色、字体、导航菜单并同步保存

### 3. 密钥管理（register-keys）
- admin/super 可生成注册密钥，指定角色（admin / super / user）
- 支持按角色、使用状态、关键词筛选；可设置有效期
- 删除密钥进入回收站，可恢复

### 4. 注册统计 & 用户管理（register-stats）
- 展示总注册用户数、各角色人数统计卡片
- 用户列表支持筛选、批量删除
- 对单个用户可：修改密码、调整页面配额、查看名下页面
- 页面管理弹窗：切换展示状态及删除页面（10 秒倒计时确认）
- 操作日志 Tab：记录所有管理操作，支持筛选，分页展示

### 5. 充值中心（recharge）— 仅 user 可见
- 展示全部套餐卡片（free / basic / pro / enterprise）
- 选择套餐后弹出 Native 扫码支付弹窗，展示 mock 二维码
- 前端每 3 秒轮询订单状态，支付成功后自动刷新当前套餐
- 演示环境：点击「我已完成支付」按钮即可立即生效套餐
- 生产环境：将后端下单逻辑替换为微信 Native 下单 API 即可，前端无需改动

### 6. 套餐管理（plan-manage）— 仅 admin/super 可见
- 查看所有用户当前套餐状态
- 可直接为任意用户切换套餐（无需支付，立即生效）
- 支持按用户名关键词、角色筛选

### 7. 回收站（trash）
- 用户、页面、密钥删除后统一进入回收站，永久保留
- 支持按类型筛选，可恢复或彻底删除
- 仅 admin / super 可见

### 8. 认证（登录 / 注册 / 忘记密码）
- 登录：用户名 + 密码 + 滑块验证码
- 注册：用户名 + 密码 + 注册密钥（一次性）
- 忘记密码：凭账号 + 注册密钥重置，无需登录

---

## 目录结构

```
apps/web-antd/
├── src/
│   ├── api/
│   │   ├── core/
│   │   │   ├── auth.ts           # 鉴权/用户/密钥/套餐/充值/回收站接口
│   │   │   ├── template.ts       # 站点页面 CRUD 接口
│   │   │   ├── user.ts           # 用户信息接口
│   │   │   ├── menu.ts           # 菜单接口
│   │   │   └── index.ts
│   │   ├── request.ts            # 请求客户端
│   │   └── index.ts
│   ├── store/
│   │   ├── template.ts           # 模板/站点页面 store
│   │   ├── auth.ts               # 鉴权 store
│   │   ├── page-config.ts        # 页面配置 store
│   │   └── index.ts
│   ├── layouts/
│   │   ├── basic.vue             # 主框架布局
│   │   ├── auth.vue              # 认证页布局
│   │   ├── blank.vue             # 空白布局
│   │   └── index.ts
│   └── views/
│       ├── dashboard/
│       │   ├── analytics/        # 模板库页面
│       │   ├── workspace/        # 模板管理工作区
│       │   ├── register-keys/    # 密钥管理
│       │   ├── register-stats/   # 用户管理 & 操作日志
│       │   ├── recharge/         # 充值中心（user 专属）
│       │   ├── plan-manage/      # 套餐管理（admin/super 专属）
│       │   └── trash/            # 回收站
│       ├── templates/
│       │   ├── template-1/config.ts
│       │   ├── template-2/config.ts
│       │   ├── template-3/config.ts
│       │   └── TemplatePreview.vue
│       ├── templateViews/
│       │   ├── index.vue
│       │   ├── Navigation.vue
│       │   ├── templateViews-1/
│       │   ├── templateViews-2/
│       │   └── templateViews-3/
│       └── _core/authentication/
│           ├── login.vue
│           ├── register.vue
│           └── forget-password.vue
└── vb项目后台/
    └── main.py                   # FastAPI 后端入口（含支付模拟接口）
```

---

## 快速启动

### 启动后端

```bash
cd apps/web-antd/vb项目后台
pip install fastapi uvicorn
python main.py
```

数据库文件 `site_pages.db` 自动创建于同目录，默认账号同步初始化。后端启动时自动检测端口冲突并终止旧进程，避免重启时端口占用。

### 启动前端

```bash
pnpm install
pnpm run dev
```

前端运行在 `http://localhost:5173`，后端运行在 `http://localhost:5666`。

### 默认账号

| 账号 | 密码 | 角色 | 说明 |
|------|------|------|------|
| admin | 123456 | admin | 超级管理员，全部权限 |
| vben | 123456 | super | 高级用户，可生成密钥管理用户 |
| jack | 123456 | user | 普通用户，默认限 1 个页面 |

---

## 账号体系

| 角色 | 权限说明 |
|------|----------|
| admin | 最高权限，管理用户、密钥、页面、套餐、回收站、操作日志 |
| super | 与 admin 等同，可生成任意角色密钥，可直接调整用户套餐 |
| user | 普通用户，默认最多创建 1 个站点页面，可通过充值升级套餐 |

**注册流程**：管理员生成注册密钥 → 分发给用户 → 用户使用密钥注册（一次性）。

**忘记密码**：登录页「忘记密码」，凭账号 + 注册密钥重置，无需管理员介入。

---

## 套餐与充值

### 套餐配置

| 套餐 | planType | 可生成页面数 | 有效期 |
|------|----------|-------------|--------|
| 免费版 | free | 1 | 30 天 |
| 基础版 | basic | 5 | 30 天 |
| 专业版 | pro | 20 | 90 天 |
| 企业版 | enterprise | 无限 | 365 天 |

### 权限规则

- `user` 角色：只能在「充值中心」选择套餐并通过支付流程升级
- `admin/super` 角色：只能在「套餐管理」直接为用户切换套餐，不能走充值流程

### 支付流程（Native 扫码）

```
user 选择套餐
  → 后端创建 pending 订单，返回 code_url
  → 前端弹出二维码弹窗（qrserver.com 渲染图片）
  → 前端每 3 秒轮询订单状态
  → 支付成功（或点击演示按钮）→ 后端发放套餐权益，订单置为 paid
  → 前端刷新当前套餐显示
```

### 接入真实微信支付

1. 申请微信商户号，获取 `mchid` 和 APIv2/v3 密钥
2. 替换后端 `create_recharge_order` 中的 `mock_code_url` 为微信 Native 下单 API 返回的真实 `code_url`
3. 新增 `POST /api/pay/notify` 回调验签接口，替代 `mock-pay` 发放权益
4. 前端无需任何改动

---

## API 接口说明

基础地址：`http://localhost:5666/api`

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /auth/login | 用户登录 |
| POST | /auth/register | 用户注册（需注册密钥）|
| POST | /auth/reset-password | 忘记密码重置 |
| POST | /auth/refresh | 刷新 Token |
| POST | /auth/logout | 退出登录 |
| GET  | /auth/codes | 获取权限码 |

### 套餐与充值

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET  | /auth/plans | 登录后 | 获取套餐列表 |
| POST | /auth/recharge-orders | user | 创建充值订单，返回 code_url |
| GET  | /auth/recharge-orders/{id} | user | 查询订单状态（轮询用）|
| POST | /auth/recharge-orders/{id}/mock-pay | user | 演示环境模拟支付成功 |
| PUT  | /auth/users/{id}/plan | admin/super | 直接修改用户套餐 |

### 用户管理（admin/super）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET    | /auth/users | 用户列表 |
| PUT    | /auth/users/{id}/password | 修改密码 |
| DELETE | /auth/users/{id} | 删除用户 |
| POST   | /auth/users/batch-delete | 批量删除 |
| GET    | /auth/users/{id}/pages | 用户名下页面 |
| GET    | /auth/users/{id}/quota | 获取配额 |
| PUT    | /auth/users/{id}/quota | 更新配额 |

### 密钥管理（admin/super）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST   | /auth/register-keys | 生成注册密钥 |
| GET    | /auth/register-keys | 密钥列表 |
| DELETE | /auth/register-keys/{id} | 删除密钥 |
| PUT    | /auth/register-keys/{id}/expires | 更新有效期 |
| GET    | /auth/register-stats | 注册统计 |

### 站点页面

| 方法 | 路径 | 说明 |
|------|------|------|
| GET    | /site-pages | 当前用户页面列表 |
| POST   | /site-pages | 创建站点页面 |
| PUT    | /site-pages/{id} | 更新站点页面 |
| DELETE | /site-pages/{id} | 删除（进回收站）|
| GET    | /site-pages/{id} | 获取详情 |
| PUT    | /auth/pages/{id}/status | 切换 published/draft |

### 公开接口（无需登录）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /public/site-pages/domain/{domain} | 通过域名获取已发布页面 |
| GET | /public/site-pages/path/{path} | 通过路径获取已发布页面 |
| GET | /public/verify-domain?domain= | 验证域名可用性 |

### 回收站（admin/super）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET    | /auth/trash | 回收站列表 |
| POST   | /auth/trash/{id}/restore | 恢复条目 |
| DELETE | /auth/trash/{id} | 彻底删除 |
| DELETE | /auth/trash | 清空回收站 |

### 操作日志（admin/super）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /auth/logs | 操作日志列表（分页+筛选）|

---

## 数据模型

### GeneratedTemplate（站点页面）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 页面唯一 ID |
| templateId | string | 使用的模板 ID |
| siteName | string | 站点名称 |
| siteDescription | string | 站点描述 |
| domain | string | 绑定域名（归一化小写）|
| navItems | NavItem[] | 导航菜单项 |
| colors | object | 配色（primary/secondary/background/text）|
| fonts | object | 字体（heading/body）|
| createdAt | string | 创建时间（ISO 8601）|
| updatedAt | string | 更新时间（ISO 8601）|

### UserQuota（用户页面配额）

| 字段 | 类型 | 说明 |
|------|------|------|
| planType | string | 套餐类型（free/basic/pro/enterprise）|
| maxPages | number | 最大可创建页面数，-1 表示无限 |
| startDate | string/null | 配额生效开始日期 |
| endDate | string/null | 配额到期日期，null 表示永久 |

### RechargeOrder（充值订单）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 订单唯一 ID |
| userId | string | 用户 ID |
| username | string | 用户名 |
| planType | string | 购买的套餐类型 |
| status | pending/paid | 订单状态 |
| createdAt | string | 创建时间 |

### TrashItem（回收站条目）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 回收站记录 ID |
| itemType | user/page/key | 条目类型 |
| itemId | string | 原始对象 ID |
| itemData | object | 被删除对象的数据快照 |
| deletedBy | string | 删除操作人 |
| deletedAt | string | 删除时间 |
| expireAt | string | 过期时间（当前为永久保留）|

---

## 三套内置模板

| 模板 | 配色 | 风格 | 适用场景 |
|------|------|------|----------|
| template-1 | 蓝色系 #0066cc/#00d4ff | 现代科技 | 科技公司、互联网企业 |
| template-2 | 黑金系 #1a1a1a/#d4af37 | 商务优雅 | 传统企业、咨询公司 |
| template-3 | 红青系 #ff6b6b/#4ecdc4 | 创意设计 | 设计公司、创意机构 |

每套模板包含：预设导航菜单（5-6 项）、配色方案、字体方案、站点缩略图。

---

## 权限控制

### 页面配额
- user 角色默认最多创建 1 个站点页面（free 套餐）
- 通过充值升级套餐可提升配额上限
- admin/super 可在「套餐管理」直接为用户切换套餐
- maxPages = -1 表示无限制
- 超出配额或到期时后端拒绝创建

### 路由权限
- 回收站、密钥管理、用户管理、套餐管理、操作日志：仅 admin/super 可见
- 充值中心：仅 user 可见
- 每个用户只能看到自己生成的站点页面

### API 权限
- 需要登录：请求头携带 `Authorization: Bearer token`
- 需要 admin/super：后端校验角色，否则返回 403
- 公开接口 `/api/public/*` 无需鉴权

---

## 回收站机制

- 删除用户、页面、密钥时，后端先将完整数据快照写入 trash 表，再执行删除
- 回收站条目永久保留（expire_at 设为 9999-12-31），不会自动清除
- 恢复时检查唯一性冲突（用户名、域名、密钥），冲突则提示无法恢复
- 支持彻底删除（不可恢复）和清空整个回收站
- 所有回收站操作均记录到操作日志

---

## 注意事项

1. **Token 安全**：使用 JWT HS256 签名，含过期时间（默认 60 分钟）。生产环境通过环境变量 `JWT_SECRET` 设置强随机密钥，`JWT_ACCESS_EXPIRE_MINUTES` 设置有效期。
2. **登录限流**：同一 IP 1 分钟内失败 5 次触发锁定，锁定时长 5 分钟，防止暴力破解。
3. **数据库**：使用 SQLite，适合中小规模；大规模建议迁移至 PostgreSQL/MySQL。
4. **密码安全**：PBKDF2-SHA256（260000 次迭代）哈希存储，旧明文密码登录时自动升级。
5. **域名验证**：通过 DNS 解析检测可用性，依赖网络环境。
6. **CORS**：通过环境变量 `ALLOWED_ORIGINS` 控制，未配置时仅允许 localhost，生产环境必须显式设置。
7. **操作日志**：静默记录，写入失败不影响主业务流程。
8. **端口冲突**：后端启动时自动检测并终止占用同端口的旧进程，开发和生产均生效。
9. **微信支付**：当前为演示模式，接入真实支付只需替换后端下单逻辑，前端零改动。

---

## 安全机制

### JWT 身份认证
- 使用 `hmac` + `hashlib` 自实现 HS256 JWT，**零第三方依赖**
- token 含用户名（`sub`）+ 过期时间（`exp`），默认有效期 60 分钟
- 签名验证失败或过期均返回 401
- refresh 接口宽限 24 小时，超出强制重新登录
- 生产环境配置：
```bash
export JWT_SECRET=your_strong_random_secret_here
export JWT_ACCESS_EXPIRE_MINUTES=30
```

### 登录限流
- 同一 IP **1 分钟内失败 5 次**触发锁定
- 锁定时长 **5 分钟**，响应 HTTP 429 并提示剩余等待秒数
- 登录成功自动清除失败记录

### CORS 配置
- 未配置时默认只允许 `localhost:5173/5174`（开发环境）
- 生产环境必须通过环境变量显式设置：
```bash
export ALLOWED_ORIGINS=https://your-frontend-domain.com
```

### 密码安全
- PBKDF2-SHA256（260000 次迭代）哈希存储
- 旧明文密码在首次登录时自动升级为哈希
- 使用 `secrets.compare_digest` 防止时序攻击

---

## 生产环境部署建议

```bash
# 设置必要环境变量
export JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
export JWT_ACCESS_EXPIRE_MINUTES=30
export ALLOWED_ORIGINS=https://your-domain.com

# 启动后端（生产不用 reload）
uvicorn main:app --host 0.0.0.0 --port 5322
```

**强烈建议生产环境加上**：
1. Nginx 反向代理 + HTTPS（Let's Encrypt 免费证书）
2. Nginx `limit_req` 全局限流（防 DDoS）
3. 定期备份 `site_pages.db` 文件

---

| 浏览器 | 支持 |
|--------|------|
| Chrome 90+ | 支持 |
| Firefox 88+ | 支持 |
| Safari 14+ | 支持 |
| Edge 90+ | 支持 |
| IE 11 | 不支持 |

---

> **项目版本**：2.2.0
> **最后更新**：2026 年 3 月