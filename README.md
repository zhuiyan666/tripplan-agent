# ✈️ 智能旅行助手

基于 AI 的个性化旅行规划工具。

## 🚀 快速启动

### 1. 环境要求

- Python ≥ 3.10 / Node.js ≥ 18
- 高德地图 API Key（[申请](https://lbs.amap.com/)）
- LLM API Key（默认 DeepSeek，兼容 OpenAI 接口）

### 2. 配置后端

```bash
cd helloagents-trip-planner/backend
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env`，填入 API Key：

```env
LLM_API_KEY=你的Key
LLM_BASE_URL=https://api.deepseek.com/v1
AMAP_API_KEY=你的高德Key
```

### 3. 启动后端

```bash
python run.py
# 后端运行在 http://localhost:8000
# API 文档: http://localhost:8000/docs
```

### 4. 启动前端

```bash
cd ../frontend
npm install
npm run dev
# 前端运行在 http://localhost:5173
```

打开浏览器访问 `http://localhost:5173`，输入目的地和偏好即可生成旅行计划。
