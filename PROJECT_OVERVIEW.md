# LLM-Filter-Probe - 项目概览

## 目录

1. [项目定位与价值](#项目定位与价值)
2. [核心能力](#核心能力)
3. [系统架构](#系统架构)
4. [技术栈](#技术栈)
5. [运行与开发](#运行与开发)
6. [目录结构](#目录结构)
7. [配置与扩展](#配置与扩展)
8. [相关文档](#相关文档)

---

## 项目定位与价值

LLM-Filter-Probe 是一款面向内容安全与风控研究的敏感词逆向定位工具。
本项目采用“宏观二分 + 微观精确定位”的混合算法，旨在通过最小化的 API 交互开销，精准还原 NEWAPI 及各类 LLM 中转服务商在用户输入侧 (Prompt) 实施的关键词拦截字典。

---

## 核心能力

- **混合算法**
  - 长文本：采用二分快速收敛定位范围
  - 短文本：双向挤压精准到词汇级
- **精准定位策略**
  - 采用“先切片，后挤压”的原则，有效处理多个敏感词紧密相邻的复杂场景。
  - 通过前向扫描隔离首个敏感目标，再对其进行精确的边界收缩，确保结果的完整性。
- **物理位置推进**
  - 扫描过程中不依赖掩码来改变文本，而是通过记录已发现词汇的坐标，从物理位置上推进扫描，确保所有坐标计算的准确性。
- **实时反馈**
  - WebSocket 推送进度与结果
- **灵活配置**
  - settings/presets/algorithm/API 多维配置，支持 user 覆盖
- **完整日志**
  - 扫描日志、导出支持，问题可追溯

---

## 系统架构

```
前端 (Vue 3 + Vite)
  ├─ 扫描界面 / 设置面板 / 日志查看
  └─ WebSocket + REST 与后端交互
        ↓
后端 (FastAPI + Python)
  ├─ 中间件：日志、错误处理、CORS
  ├─ 路由层：REST API / WebSocket
  ├─ 服务层：ScanService
  ├─ 核心层：TextScanner / BinarySearcher / PrecisionScanner
  └─ 配置系统：ConfigManager (credentials/settings/presets/algorithm)
        ↓
上游 LLM API（OpenAI / 中转服务）
```

分层职责（简表）：
- 中间件：统一日志、异常、跨域
- 路由层：对外 API 与 WS 事件
- 服务层：业务编排与会话管理
- 核心层：算法引擎与策略选择
- 配置层：集中加载、合并与热重载

---

## 技术栈

- 后端：Python 3.11+、FastAPI、Uvicorn/Gunicorn
- 前端：Vue 3、Vite、Pinia
- 通信：REST + WebSocket
- 部署：一键脚本 / Docker Compose / Nginx+Gunicorn（生产）

---

## 运行与开发

优先推荐使用一键脚本（自动安装依赖并启动前后端）：

- Windows：
```bash
start_system.bat
```
- macOS / Linux：
```bash
bash start_system.sh
```

访问地址：
```
http://localhost:19001
```

手动方式（可选）：
- 终端 1（后端）
```bash
cd backend
# Windows: venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
python -m uvicorn main:app --reload
```
- 终端 2（前端）
```bash
cd frontend
npm run dev
```

更多部署方式见《DEPLOYMENT_GUIDE.md》。

---

## 目录结构

```
LLM-Filter-Probe/
├── backend/
│   ├── core/
│   │   ├── engine/                # API 探测/构建/分析/重试
│   │   ├── scanner/               # 宏观二分/微观精确定位/扫描协调器
│   │   ├── config_manager.py      # 配置管理与热重载
│   │   ├── event_bus.py           # 事件总线
│   │   └── constants.py           # 常量
│   ├── routes/ (api.py, websocket.py)
│   ├── services/ (scan_service.py)
│   ├── middleware/ (logging.py, error_handler.py)
│   ├── models/ (request.py, response.py)
│   ├── app.py / main.py
│   
├── frontend/
│   └── src/ (components / stores / utils / constants / App.vue / main.js)
│
├── config/
│   ├── API/credentials.json
│   ├── settings/{default.json, user.json}
│   ├── presets/{official.json, relay.json, custom.json}
│   └── algorithm/default.json
│
├── docs/ (ALGORITHM.md / ARCHITECTURE.md / CONFIGURATION.md / QUICKSTART.md)
├── DEPLOYMENT_GUIDE.md
├── PARAMETER_REFERENCE.md
├── PROJECT_OVERVIEW.md
├── docker-compose.yml
├── requirements.txt
├── start_system.bat
└── start_system.sh
```

---

## 配置与扩展

- 配置来源与优先级：
  1) settings/default.json（系统默认）
  2) settings/user.json（用户覆盖）
  3) presets/*（拦截/重试规则）
  4) algorithm/default.json（算法参数）
  5) API/credentials.json（上游地址与密钥）
- 热重载：每次扫描前重新加载配置，修改后无需重启
- 可扩展点：
  - 扫描策略：新增策略并在策略选择器中注册
  - 预设规则：新增/调整 block/retry 规则集
  - 引擎适配：为不同上游 API 增加请求/响应适配器


## 相关文档

- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - 部署与运维指南（默认一键脚本）
- [PARAMETER_REFERENCE.md](./PARAMETER_REFERENCE.md) - 参数与调优手册

