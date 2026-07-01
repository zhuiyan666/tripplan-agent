# 智能旅行助手 - 产品需求文档 (PRD)

## 1. 项目概述

### 1.1 目标
构建一个完整的智能旅行助手Web应用，用户输入目的地、日期、偏好等信息，系统自动生成包含景点、餐饮、酒店的完整行程计划，并提供地图可视化、预算计算、行程编辑和导出功能。

### 1.2 技术架构
- **前端层**: Vue 3 + TypeScript + Ant Design Vue + 高德地图 JS API
- **后端层**: FastAPI + Python 3.10+
- **智能体层**: HelloAgents 框架（4个专门Agent协作）
- **外部服务层**: 高德地图 API（MCP协议）、Unsplash API、LLM API

## 2. 数据模型

### 2.1 Pydantic 模型（后端）
```
Location          - 经纬度坐标（经度、纬度）
Attraction        - 景点信息（名称、地址、位置、游览时间、描述、类别、评分、图片URL、门票价格）
Meal              - 餐饮信息（类型、名称、地址、位置、描述、预估费用）
Hotel             - 酒店信息（名称、地址、位置、价格范围、评分、距离、类型、预估费用）
Budget            - 预算信息（景点门票、酒店、餐饮、交通、总费用）
WeatherInfo       - 天气信息（日期、白天天气、夜间天气、白天温度、夜间温度、风向、风力）
DayPlan           - 单日行程（日期、第几天、描述、交通方式、住宿安排、酒店、景点列表、餐饮安排）
TripPlan          - 完整旅行计划（城市、开始日期、结束日期、每日行程、天气信息、总体建议、预算）
TripPlanRequest   - 旅行请求（城市、开始日期、结束日期、天数、偏好、预算级别、交通方式、住宿类型）
```

### 2.2 TypeScript 接口（前端）
与后端Pydantic模型一一对应的 interface 定义。

## 3. 智能体协作设计

### 3.1 四个专门Agent
1. **AttractionSearchAgent** - 景点搜索专家：根据用户偏好搜索景点
2. **WeatherQueryAgent** - 天气查询专家：查询目的地天气
3. **HotelAgent** - 酒店推荐专家：根据住宿类型搜索酒店
4. **PlannerAgent** - 行程规划专家：整合所有信息生成完整行程

### 3.2 协作流程
```
用户请求 → AttractionSearchAgent（景点搜索）→ WeatherQueryAgent（天气查询）→ HotelAgent（酒店搜索）→ PlannerAgent（整合规划）→ 返回 TripPlan
```

### 3.3 共享MCP实例
三个数据获取Agent共享同一个高德地图MCP工具实例，通过 `MCPTool` 的 `auto_expand=True` 自动获取16个工具。

## 4. API 接口

### 4.1 核心接口
- `POST /api/trip/plan` - 生成旅行计划（请求：TripPlanRequest，响应：TripPlan）

## 5. 前端功能

### 5.1 页面
- **Home.vue** - 首页表单（目的地、日期、偏好、预算、交通、住宿）
- **Result.vue** - 结果展示页（行程概览、预算明细、地图、每日行程、天气）

### 5.2 核心功能
- **地图可视化**: 高德地图标注景点位置、绘制路线
- **预算计算**: 自动计算门票、酒店、餐饮、交通费用
- **行程编辑**: 添加、删除、调整景点顺序，实时更新地图
- **导出功能**: 导出为PDF或图片（html2canvas + jsPDF）
- **侧边导航**: 锚点跳转快速定位各模块
- **加载进度**: 模拟进度条展示规划状态

## 6. 外部服务集成

### 6.1 高德地图MCP
- 工具: `amap_maps_text_search`, `amap_maps_weather`, 等16个工具
- 启动方式: `npx -y @sugarforever/amap-mcp-server`
- 环境变量: `AMAP_API_KEY`

### 6.2 Unsplash API
- 用途: 为景点获取图片
- 接口: `/search/photos`
- 密钥: `UNSPLASH_ACCESS_KEY`

### 6.3 LLM API
- 用途: Agent推理和决策
- 支持: OpenAI、DeepSeek等

## 7. 项目结构

```
helloagents-trip-planner/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── trip_planner.py      # TripPlannerAgent（主协调器）
│   │   │   └── prompts.py           # Agent提示词
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── main.py              # FastAPI入口
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       └── trip.py          # 旅行规划路由
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py           # Pydantic模型
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── unsplash_service.py  # Unsplash图片服务
│   │   └── config.py                # 配置管理
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
│
└── frontend/
    ├── src/
    │   ├── views/
    │   │   ├── Home.vue               # 首页表单
    │   │   └── Result.vue             # 结果页
    │   ├── services/
    │   │   └── api.ts                 # API封装
    │   ├── types/
    │   │   └── index.ts               # TypeScript类型
    │   ├── router/
    │   │   └── index.ts               # 路由配置
    │   ├── App.vue
    │   └── main.ts
    ├── package.json
    ├── vite.config.ts
    └── tsconfig.json
```

## 8. 环境要求
- Python 3.10+
- Node.js 16.0+
- npm 8.0+

## 9. API密钥需求
- LLM API Key（OpenAI / DeepSeek）
- 高德地图 Web 服务 Key
- Unsplash Access Key
