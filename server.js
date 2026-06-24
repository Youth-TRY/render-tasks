import express from 'express';
import { exec, execSync } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { writeFileSync, existsSync } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = process.env.PORT || 3000;
const API_KEY = process.env.API_KEY || 'youthtry-task-2026';

// ── 初始化：从环境变量创建配置文件 ─────────────
function initConfig() {
  // 微信公众号配置
  const appid = process.env.WECHAT_APPID;
  const secret = process.env.WECHAT_SECRET;
  if (appid && secret) {
    const config = { appid, secret };
    writeFileSync(join(__dirname, 'config', 'wechat_mp.json'), JSON.stringify(config, null, 2));
    console.log('✓ WeChat config created');
  }

  // 创建工作目录
  const dirs = ['output', 'output/articles', 'output/covers'];
  for (const dir of dirs) {
    const path = join(__dirname, dir);
    if (!existsSync(path)) {
      execSync(`mkdir -p ${path}`);
    }
  }
}

initConfig();

// ── 中间件 ──────────────────────────────────────
app.use(express.json());

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
    env: {
      hasWechat: !!(process.env.WECHAT_APPID && process.env.WECHAT_SECRET),
      hasMxKey: !!process.env.MX_APIKEY,
      hasAiKey: !!process.env.AI_API_KEY,
    }
  });
});

// ── 任务注册 ────────────────────────────────────
const taskRegistry = {
  'daily-article':  { desc: '每日选题+文章推送', script: 'daily_topic_selection_v2.py', args: '--auto' },
  'daily-weibo':    { desc: '微博热点获取', script: null, handler: handleWeibo },
  'weekly-display': { desc: '显示产业链周报', script: null, handler: handleWeeklyDisplay },
  'weekly-agent':   { desc: 'Agent产业链周报', script: null, handler: handleWeeklyAgent },
  'weekly-robot':   { desc: '机器人行业周报', script: null, handler: handleWeeklyRobot },
  'invest-open':    { desc: '投资决策-开盘', script: null, handler: handleInvestOpen },
  'invest-close':   { desc: '投资决策-收盘', script: null, handler: handleInvestClose },
};

// ── 执行Python脚本 ──────────────────────────────
function runPythonScript(scriptName, args, res) {
  const scriptPath = join(__dirname, 'scripts', scriptName);
  const cmd = `python3 ${scriptPath} ${args || ''}`;
  const start = Date.now();

  console.log(`[${new Date().toISOString()}] ▶ ${scriptName}: ${cmd}`);

  exec(cmd, {
    cwd: __dirname,
    timeout: 300000,
    env: {
      ...process.env,
      WORKSPACE_DIR: __dirname,
      ARTICLES_DIR: join(__dirname, 'articles'),
      OUTPUT_DIR: join(__dirname, 'output'),
      PYTHONUNBUFFERED: '1',
    }
  }, (err, stdout, stderr) => {
    const elapsed = ((Date.now() - start) / 1000).toFixed(1);
    if (err) {
      console.error(`[${new Date().toISOString()}] ✗ ${scriptName} (${elapsed}s):`, err.message);
    } else {
      console.log(`[${new Date().toISOString()}] ✓ ${scriptName} (${elapsed}s)`);
    }
    if (stdout) console.log(stdout.slice(-1000));
    if (stderr) console.error(stderr.slice(-500));
  });

  return {
    accepted: true,
    task: scriptName,
    message: 'Task queued, check Render logs for result'
  };
}

// ── 占位handler（后续实现）───────────────────────
function handleWeibo(req, res) {
  res.json({ accepted: true, task: 'daily-weibo', message: 'Not implemented yet' });
}
function handleWeeklyDisplay(req, res) {
  res.json({ accepted: true, task: 'weekly-display', message: 'Not implemented yet' });
}
function handleWeeklyAgent(req, res) {
  res.json({ accepted: true, task: 'weekly-agent', message: 'Not implemented yet' });
}
function handleWeeklyRobot(req, res) {
  res.json({ accepted: true, task: 'weekly-robot', message: 'Not implemented yet' });
}
function handleInvestOpen(req, res) {
  res.json({ accepted: true, task: 'invest-open', message: 'Not implemented yet' });
}
function handleInvestClose(req, res) {
  res.json({ accepted: true, task: 'invest-close', message: 'Not implemented yet' });
}

// ── 任务路由 ────────────────────────────────────
function handleTask(req, res) {
  const name = req.params.name;
  const task = taskRegistry[name];

  if (!task) {
    return res.status(404).json({ error: `Unknown task: ${name}` });
  }

  if (task.handler) {
    return task.handler(req, res);
  }

  if (task.script) {
    const result = runPythonScript(task.script, task.args, res);
    return res.json(result);
  }

  res.status(500).json({ error: 'No handler for task' });
}

app.post('/task/:name', auth, handleTask);
app.get('/task/:name', auth, handleTask);

// ── 任务列表 ────────────────────────────────────
app.get('/tasks', auth, (req, res) => {
  const list = {};
  for (const [k, v] of Object.entries(taskRegistry)) {
    list[k] = v.desc;
  }
  res.json(list);
});

// ── 启动 ────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`\n🚀 YouthTRY Task Runner`);
  console.log(`   Port: ${PORT}`);
  console.log(`   Auth: x-api-key = ${API_KEY}`);
  console.log(`   Tasks: ${Object.keys(taskRegistry).length} registered`);
  console.log(`   WeChat: ${process.env.WECHAT_APPID ? '✓' : '✗'}`);
  console.log(`   MX API: ${process.env.MX_APIKEY ? '✓' : '✗'}`);
  console.log(`   AI API: ${process.env.AI_API_KEY ? '✓' : '✗'}\n`);
});
