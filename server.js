import express from 'express';
import { exec } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = process.env.PORT || 3000;
const API_KEY = process.env.API_KEY || 'youthtry-task-2026';

// ── 中间件 ──────────────────────────────────────
app.use(express.json());

// API Key 认证
function auth(req, res, next) {
  const key = req.headers['x-api-key'] || req.query.key;
  if (key !== API_KEY) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
}

// ── 健康检查 ────────────────────────────────────
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    uptime: Math.floor(process.uptime()),
    tasks: Object.keys(taskRegistry)
  });
});

// ── 任务执行器 ──────────────────────────────────
const taskRegistry = {
  // 每日任务
  'daily-article':   '每日选题+文章',
  'daily-weibo':     '微博热点',

  // 每周任务
  'weekly-display':  '显示产业链周报',
  'weekly-agent':    'Agent产业链周报',
  'weekly-robot':    '机器人行业周报',

  // 投资
  'invest-open':     '投资决策-开盘',
  'invest-close':    '投资决策-收盘',
};

function runTask(taskName, res) {
  const scriptMap = {
    'daily-article':  'python3 daily_topic_selection_v2.py --auto',
    'daily-weibo':    'python3 weibo_hot_topics.py',
    'weekly-display': 'python3 weekly_report_display.py',
    'weekly-agent':   'python3 weekly_report_agent.py',
    'weekly-robot':   'python3 weekly_report_robot.py',
    'invest-open':    'python3 invest_decision.py --time open',
    'invest-close':   'python3 invest_decision.py --time close',
  };

  const cmd = scriptMap[taskName];
  if (!cmd) {
    return res.status(404).json({ error: `Unknown task: ${taskName}` });
  }

  const start = Date.now();
  const scriptsDir = join(__dirname, '..', 'scripts');

  console.log(`[${new Date().toISOString()}] ▶ ${taskName}: ${cmd}`);

  // 异步执行，立即返回
  exec(cmd, { cwd: scriptsDir, timeout: 300000 }, (err, stdout, stderr) => {
    const elapsed = ((Date.now() - start) / 1000).toFixed(1);
    if (err) {
      console.error(`[${new Date().toISOString()}] ✗ ${taskName} (${elapsed}s):`, err.message);
    } else {
      console.log(`[${new Date().toISOString()}] ✓ ${taskName} (${elapsed}s)`);
    }
    if (stdout) console.log(stdout.slice(-500));
    if (stderr) console.error(stderr.slice(-500));
  });

  res.json({
    accepted: true,
    task: taskName,
    description: taskRegistry[taskName],
    message: 'Task queued, check logs for result'
  });
}

// ── 任务路由 ────────────────────────────────────
app.post('/task/:name', auth, (req, res) => {
  runTask(req.params.name, res);
});

// ── 批量触发（cron-job.org 可能只支持 GET）──────
app.get('/task/:name', auth, (req, res) => {
  runTask(req.params.name, res);
});

// ── 任务列表 ────────────────────────────────────
app.get('/tasks', auth, (req, res) => {
  res.json(taskRegistry);
});

// ── 启动 ────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`\n🚀 YouthTRY Task Runner`);
  console.log(`   Port: ${PORT}`);
  console.log(`   Auth: x-api-key = ${API_KEY}`);
  console.log(`   Tasks: ${Object.keys(taskRegistry).length} registered\n`);
});
