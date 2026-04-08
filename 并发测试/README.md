# 并发测试

这个目录用于对你的站点或接口做简单压力测试。

当前提供的是一个纯 Python 版本压测脚本，不依赖 `wrk`、`ab`、`k6`，适合你当前 Windows 环境直接运行。

## 文件说明

- `stress_test.py`：HTTP 并发压力测试脚本

## 当前脚本特点

这个版本默认会模拟真实浏览器请求头，适合测试你当前重点接口：

- `/api/public/site-pages/domain/www.dyzpt.xyz`

默认会自动带上：

- `User-Agent`（Chrome 风格）
- `Accept`
- `Accept-Language`
- `Cache-Control`
- `Pragma`
- `Connection`
- `Upgrade-Insecure-Requests`
- `Referer`

这样比之前更接近真实用户访问，也更不容易被你自己的反爬策略误判成脚本流量。

## 使用方式

当前目录是：

- `D:/项目/vue-vben-admin-main/apps/web-antd/并发测试`

你可以直接执行下面命令。

## 1. 测你当前最关心的公开页面接口

```bash
python "D:/项目/vue-vben-admin-main/apps/web-antd/并发测试/stress_test.py" --url http://127.0.0.1:5322/api/public/site-pages/domain/www.dyzpt.xyz --total 100 --concurrency 10
```

## 2. 中等并发测试

```bash
python "D:/项目/vue-vben-admin-main/apps/web-antd/并发测试/stress_test.py" --url http://127.0.0.1:5322/api/public/site-pages/domain/www.dyzpt.xyz --total 300 --concurrency 20
```

## 3. 更高并发测试

```bash
python "D:/项目/vue-vben-admin-main/apps/web-antd/并发测试/stress_test.py" --url http://127.0.0.1:5322/api/public/site-pages/domain/www.dyzpt.xyz --total 500 --concurrency 50
```

## 4. 指定来源页 Referer

如果你想让请求更像从前端页面点击进入，可以手动指定 Referer：

```bash
python "D:/项目/vue-vben-admin-main/apps/web-antd/并发测试/stress_test.py" --url http://127.0.0.1:5322/api/public/site-pages/domain/www.dyzpt.xyz --total 100 --concurrency 10 --referer http://www.dyzpt.xyz:5666/
```

## 5. 额外附加请求头

比如你后面想带 Cookie 或其他头，可以重复传 `--header`：

```bash
python "D:/项目/vue-vben-admin-main/apps/web-antd/并发测试/stress_test.py" --url http://127.0.0.1:5322/api/public/site-pages/domain/www.dyzpt.xyz --total 100 --concurrency 10 --header "Cookie:test=1" --header "X-Requested-With:XMLHttpRequest"
```

## 6. 输出结果到 JSON 文件

```bash
python "D:/项目/vue-vben-admin-main/apps/web-antd/并发测试/stress_test.py" --url http://127.0.0.1:5322/api/public/site-pages/domain/www.dyzpt.xyz --total 300 --concurrency 20 --output result.json
```

## 参数说明

- `--url`：目标地址，必填
- `--total`：总请求数，默认 `200`
- `--concurrency`：并发数，默认 `20`
- `--timeout`：单个请求超时秒数，默认 `10`
- `--output`：可选，将结果输出为 JSON 文件
- `--referer`：可选，模拟来源页面，默认 `http://www.dyzpt.xyz:5666/`
- `--header`：可重复传入自定义请求头，格式 `Header:Value`

## 推荐测试梯度

建议按下面顺序逐步测试你这个公开接口：

### 第一轮

```bash
python "D:/项目/vue-vben-admin-main/apps/web-antd/并发测试/stress_test.py" --url http://127.0.0.1:5322/api/public/site-pages/domain/www.dyzpt.xyz --total 100 --concurrency 10
```

### 第二轮

```bash
python "D:/项目/vue-vben-admin-main/apps/web-antd/并发测试/stress_test.py" --url http://127.0.0.1:5322/api/public/site-pages/domain/www.dyzpt.xyz --total 200 --concurrency 20
```

### 第三轮

```bash
python "D:/项目/vue-vben-admin-main/apps/web-antd/并发测试/stress_test.py" --url http://127.0.0.1:5322/api/public/site-pages/domain/www.dyzpt.xyz --total 500 --concurrency 50
```

## 结果怎么看

脚本会输出这些指标：

- 总请求数
- 并发数
- 总耗时
- QPS
- 成功数 / 失败数
- 成功率
- 平均延迟
- 最小 / 最大延迟
- P50 / P95 / P99 延迟
- 状态码分布
- 错误分布
- 本次使用的请求头

## 注意事项

### 1. 你这个后端本身有安全限流

代码里已经有：

- 全局限流
- 单路径限流
- 反爬拦截

所以压测时如果出现：

- `429`
- `403`

不一定是接口扛不住，也可能是你自己的安全策略生效。

### 2. 当前脚本只是尽量模拟真实浏览器

它会比默认 Python 请求头更像用户访问，但仍然不是完整浏览器环境，没有：

- JS 执行
- Cookie 自动协商
- 真实页面资源联动加载

所以它适合测接口吞吐，不等于完整浏览器端页面压测。

### 3. 如果你要测接口极限能力

建议临时调大这些配置，否则你测到的是“防护效果”：

- `GLOBAL_RATE_LIMIT`
- `CC_PATH_RATE_LIMIT`
- `BOT_SCORE_BLOCK`

## 建议结论标准

### 说明接口还可以

- 成功率高
- 95 分位延迟可接受
- 没有大量 `500 / 502 / 504`
- 没有大量超时

### 说明接口开始吃紧

- 大量 `429 / 403`
- 延迟明显升高
- 错误率明显上升
- 超时增多

如果你需要，我下一步还可以继续帮你加：

1. 自动分阶段压测
2. 输出 CSV / JSON 汇总
3. 多 URL 混合压测
4. 带 Cookie / Token 的压测
