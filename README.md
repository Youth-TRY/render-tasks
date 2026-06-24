# YouthTRY Task Runner

公众号自动化定时任务服务，部署在 Render 上，通过 cron-job.org 定时触发。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/tasks` | 任务列表 |
| GET/POST | `/task/:name` | 执行任务 |

## 任务列表

| 任务名 | 说明 | 建议调度 |
|--------|------|----------|
| `daily-article` | 每日选题+文章推送 | 每天 07:00 |
| `daily-weibo` | 微博热点获取 | 每天 08:00 |
| `weekly-display` | 显示产业链周报 | 每周日 19:00 |
| `weekly-agent` | Agent产业链周报 | 每周三 19:00 |
| `weekly-robot` | 机器人行业周报 | 每周日 18:00 |
| `invest-open` | 投资决策-开盘 | 周一至五 08:00 |
| `invest-close` | 投资决策-收盘 | 周一至五 15:00 |

## 调用示例

```bash
curl -H "x-api-key: youthtry-task-2026" https://your-app.onrender.com/task/daily-article
```

## 部署

1. Push 到 GitHub
2. Render → New Web Service → 选仓库
3. 设置环境变量 API_KEY
4. Deploy
5. 在 cron-job.org 创建定时任务
