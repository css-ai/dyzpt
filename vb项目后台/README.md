# vb项目后台

这是一个基于 `FastAPI` 的站点页面后端服务，用于支持“企业门户/模板站点”的创建、发布、公开访问、用户注册登录、套餐配额和基础安全防护。

当前 README 已清理旧的历史对话导出内容，仅保留与当前代码一致的说明，并补充目前已经实现的功能。

## 目录结构

```text
vb项目后台/
├─ main.py            # 后端主程序
├─ requirements.txt   # Python 依赖
├─ site_pages.db      # 早期/兼容用本地数据库文件
└─ README.md          # 项目说明
```

## 技术栈

- `FastAPI`
- `Pydantic`
- `PyMySQL`
- `Redis`
- `psutil`
- `SQLite`（仅保留兼容痕迹）

## 当前已实现的功能

### 1. 页面管理

已实现站点页面的完整基础管理能力：

- 创建页面：`POST /api/site-pages`
- 更新页面：`PUT /api/site-pages/{page_id}`
- 删除页面：`DELETE /api/site-pages/{page_id}`
- 获取当前用户页面列表：`GET /api/site-pages`
- 获取单个页面详情：`GET /api/site-pages/{page_id}`

页面数据当前包含以下核心字段：

- `site_path`：公开访问路径
- `bind_domain`：绑定域名
- `site_name`：站点名称
- `site_description`：站点描述
- `template_id`：模板 ID
- `nav_items`：导航配置
- `colors`：颜色配置
- `fonts`：字体配置
- `status`：页面状态，支持 `draft` / `published`
- `owner_username`：所属用户

### 2. 公开访问接口

已实现公开页面读取能力，无需登录即可访问已发布页面：

- 按路径读取：`GET /api/public/site-pages/path/{site_path}`
- 按绑定域名读取：`GET /api/public/site-pages/domain/{domain}`
- 兼容旧接口：`GET /api/public/site-pages/{site_path}`

说明：

- 仅 `published` 状态的页面可公开访问
- 域名接口会自动做归一化处理
- 如果页面不存在或未发布，会返回 `404`

### 3. 用户认证与注册

已实现基础后台认证体系：

- 登录：`POST /api/auth/login`
- 注册：`POST /api/auth/register`

认证能力包括：

- JWT 登录认证
- 密码哈希存储（PBKDF2-SHA256）
- 旧明文密码登录后自动升级为哈希密码
- 基于 `Authorization: Bearer <token>` 的登录态识别

### 4. 注册密钥机制

已实现“注册密钥”控制注册能力：

- 创建注册密钥：`POST /api/auth/register-keys`
- 注册统计：`GET /api/auth/register-stats`

特性：

- 只有管理员可生成注册密钥
- 注册时必须提供有效密钥
- 密钥使用后会标记为已使用
- 支持按角色生成密钥：`admin` / `super` / `user`

### 5. 套餐与页面配额

已实现用户套餐与页面生成额度管理：

- 获取套餐列表：`GET /api/auth/plans`
- 创建充值订单：`POST /api/auth/recharge-orders`
- 模拟支付成功：`POST /api/auth/recharge-orders/{order_id}/mock-pay`
- 查询订单状态：`GET /api/auth/recharge-orders/{order_id}`
- 管理员直接修改用户套餐：`PUT /api/auth/users/{user_id}/plan`
- 查看用户配额：`GET /api/auth/users/{user_id}/quota`
- 修改用户配额：`PUT /api/auth/users/{user_id}/quota`

当前内置套餐：

- `free`
- `basic`
- `pro`
- `enterprise`

支持能力：

- 控制用户最大可创建页面数
- 控制套餐生效时间范围
- 普通用户受配额限制
- `admin` / `super` 默认可拥有无限页面权限

### 6. 用户管理增强

目前已实现部分管理员用户管理能力：

- 管理员修改用户密码：`PUT /api/auth/users/{user_id}/password`
- 管理员强制用户下线：`POST /api/auth/users/{user_id}/force-logout`

说明：

- 修改密码后，历史 token 会失效
- 强制下线通过 JWT 版本号机制实现

### 7. 回收站与软删除

已实现回收站机制：

- 页面删除时不会直接丢弃快照，而是先写入回收站
- 当前 `trash` 表可用于后续恢复或审计
- 当前设置为长期保留，不自动清理

### 8. 操作日志

已实现操作日志记录：

- 删除页面记录日志
- 创建充值订单记录日志
- 模拟支付记录日志
- 修改套餐/配额/密码等管理员操作记录日志

数据保存在：

- `operation_logs` 表

### 9. 安全防护

当前代码已经加入一套生产可用的基础安全能力：

#### 全局限流

- 基于 Redis 的 IP 维度限流
- 超限返回 `429`

#### CC 防护

- 基于 `IP + Path` 的高频访问限制
- 防止单一路径被高并发刷接口

#### 登录防暴力破解

- 登录失败次数写入 Redis
- 连续失败后自动锁定 IP 一段时间
- 登录成功后自动清除失败计数

#### JWT 安全增强

- token 支持 `jti`
- token 支持版本号 `ver`
- 支持 token 黑名单
- 支持强制下线

#### 反爬与机器人拦截

- 基于 `User-Agent` 和请求特征进行基础风险评分
- 对高风险请求进行拦截
- 触发后写入安全事件日志

#### 安全响应头

已设置：

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy`
- `Strict-Transport-Security`（开启 HTTPS 时）

#### CORS 白名单

- 仅允许白名单来源跨域
- 仅开放指定 methods / headers

#### Host 白名单

- 已启用 `TrustedHostMiddleware`
- 可通过环境变量限制允许访问的 Host

#### HTTPS 跳转

- 可选启用 `HTTPSRedirectMiddleware`
- 生产环境建议开启

#### 安全事件日志

已实现安全事件记录：

- 限流拦截
- CC 拦截
- 登录失败
- 机器人拦截

数据保存在：

- `security_events` 表

## 数据表概览

当前代码中会自动初始化这些主要数据表：

- `site_pages`：站点页面
- `users`：用户
- `register_keys`：注册密钥
- `user_page_quota`：用户页面配额
- `recharge_orders`：充值订单
- `operation_logs`：操作日志
- `security_events`：安全事件
- `trash`：回收站

## 默认用户

启动初始化时，如果用户表为空，会注入默认用户。

默认账号包括：

- `admin`
- `vben`
- `jack`

默认密码在初始化阶段会被哈希后存储。

> 如果你是正式部署，建议初始化后立即修改默认密码，或删除默认账号逻辑。

## 运行依赖

安装依赖：

```bash
pip install -r requirements.txt
```

当前依赖如下：

```txt
fastapi==0.116.1
uvicorn==0.35.0
pydantic==2.12.5
psutil==6.1.1
pymysql==1.1.1
redis==5.2.1
```

## 启动方式

在 `vb项目后台` 目录下执行：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 5322
```

代码中默认读取：

- `API_HOST`，默认 `127.0.0.1`
- `API_PORT`，默认 `5322`

启动时会执行：

- 自动清理同端口冲突旧进程
- 自动初始化数据库结构
- 自动初始化默认用户

## 环境变量说明

### 基础配置

- `APP_ENV`：运行环境，默认 `development`
- `API_HOST`：服务监听地址
- `API_PORT`：服务监听端口
- `DATABASE_URL`：数据库连接串
- `REDIS_URL`：Redis 地址
- `JWT_SECRET`：JWT 密钥
- `ALLOWED_ORIGINS`：CORS 白名单
- `ALLOWED_HOSTS`：Host 白名单

### 安全配置

- `FORCE_HTTPS`：是否强制 HTTPS
- `TRUST_PROXY_HEADERS`：是否信任代理头
- `GLOBAL_RATE_LIMIT`：全局限流阈值
- `GLOBAL_RATE_WINDOW_SEC`：全局限流窗口
- `CC_PATH_RATE_LIMIT`：单路径限流阈值
- `CC_PATH_RATE_WINDOW_SEC`：单路径限流窗口
- `LOGIN_MAX_FAIL`：登录失败上限
- `LOGIN_WINDOW_SEC`：登录失败统计窗口
- `LOGIN_LOCK_SEC`：登录锁定时长
- `JWT_BLACKLIST_TTL_SEC`：JWT 黑名单缓存时长
- `LOG_LEVEL`：日志级别

### 当前代码中的默认连接示例

- MySQL：`mysql://root:123456@127.0.0.1:3306/template_cms`
- Redis：`redis://127.0.0.1:6379/0`

正式部署前请改成真实配置，不建议直接使用默认值。

## 健康检查接口

已实现基础健康检查：

- `GET /health`
- `GET /api/status`

返回：

```json
{"status":"ok"}
```

## 生产环境说明

当 `APP_ENV=production` 时：

- 必须显式配置 `JWT_SECRET`
- 必须显式配置 `ALLOWED_ORIGINS`
- `docs` / `redoc` / `openapi.json` 会关闭
- 建议同时配置：
  - `ALLOWED_HOSTS`
  - `FORCE_HTTPS=1`
  - 正式 MySQL 与 Redis

## 已删除的旧内容

以下旧 README 内容已经删除，不再适用：

- 历史聊天记录导出
- 与当前后端无关的前端项目总结
- 已不存在文件的说明
- 早期错误排查过程记录
- 与当前代码不一致的旧部署描述

## 备注

当前 `main.py` 中仍保留了部分早期 SQLite 兼容逻辑与后续 MySQL 接管逻辑，但实际统一连接已经切换为 MySQL 方式。

如果你后续需要，我可以继续帮你补两部分文档：

1. 完整接口表格版文档
2. 服务器部署文档（Windows / Linux / 宝塔 / Nginx）
