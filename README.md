# cloud_eai_server — 边缘 AI 视频分析集群管理平台（云智 eai）

> **产品标识**：`cloud_eai_admin` ｜ **版本**：v2.7 ｜ **构建日期**：2025/12/04 ｜ **最近更新**：2026/10/18（新增中/英多语言切换）
> **最低支持节点版本**：v2.3.6
> **官方站点**：https://www.yunzhieai.com/

`cloud_eai_server`（内部代号 `cloud_edgeai`）是一套基于「云-边」架构的边缘 AI 视频分析**集群管理平台**。本工程为**云端管理端（Admin）**，负责对分布在各边缘节点的 AI 视频分析设备进行统一接入、监控、任务下发与数据汇聚，并提供 Web 管理界面、流媒体网关以及对外开放 API 等能力。

---

## 1. 系统架构

```
                         ┌────────────────────────────────────────────┐
                         │                Web 云平台 / 集群平台          │
                         │          （设备发现 / 数据同步 / 任务管理）      │
                         └───────────────────┬────────────────────────┘
                                             │  HTTP API（Eai-Secret / Safe 鉴权）
                                             ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                         本工程：云端管理端（Admin / Django 4.2）             │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │
│  │ 用户/登录   │ │ 节点管理   │ │ 视频流管理 │ │ 布控管理   │ │ 报警管理   │   │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘   │
│  ┌───────────┐ ┌───────────┐ ┌─────────────────────────────────────┐   │
│  │ 仪表盘     │ │ 系统/版本  │ │           开放接口 open/*              │   │
│  └───────────┘ └───────────┘ └─────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                  MySQL 8.0（业务数据） eai_* 表                    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
        │
        │ HTTP（Safe 头 + eai_safe）
        ▼
┌───────────────────┐
│ 边缘 AI 节点        │
│ eai_node        │
│ 视频采集/算法分析    │
└───────────────────┘
```

### 1.1 分层说明

| 层 | 组件 | 说明 |
| --- | --- | --- |
| 管理端（云端） | `admin/`（Django 4.2） | 本工程核心：Web 界面 + 业务 API + 开放接口 |
| 边缘节点 | `eai_node` | 部署在边缘设备的 AI 视频分析服务，通过 HTTP 与云端通信 |
| 流媒体网关 | `zlmediakit/` | ZLMediaKit，统一提供 RTSP / HLS / HTTP-FLV / WS-MP4 拉流与转推 |
| 业务数据库 | MySQL 8.0 | 存储节点、报警、视频流、算法流、用户等业务数据 |

### 1.2 数据流

- **上行（节点 → 云端）**：节点上报媒体源、报警（签名推送 `/alarm/openPush` + 媒体上传 `/alarm/openUploadFile`）、计数统计（`/alarm/openPush` / `/alarm/openResetCount` 周期清零归档）与核心进程数据；云端通过 `open/*` 接口采集汇总。
- **下行（云端 → 节点）**：云端向节点下发布控任务（启动/停止/删除）、视频流转发/转推代理指令。

---

## 2. 目录结构

```
cloud_eai_server/
├── admin/                        # 云端管理端主应用（Django 项目）
│   ├── manage.py                 # Django 管理入口
│   ├── config.json               # 运行配置（端口、ZLM 密钥、目录等）
│   ├── settings.json             # 系统显示配置（名称、Logo、作者等）
│   ├── .db.json                  # MySQL 连接配置
│   ├── framework/                # Django 项目配置（settings / urls / wsgi）
│   ├── app/                      # 业务应用
│   │   ├── models.py             # 数据模型（8 张业务表，另有 eai_log 走原生 SQL）
│   │   ├── urls.py               # 路由（含集群平台对接接口）
│   │   ├── middleware.py         # 登录拦截 + 会话中间件
│   │   ├── views/                # 视图（按业务模块拆分）
│   │   │   ├── IndexView.py      #   仪表盘
│   │   │   ├── UserView.py       #   用户/登录
│   │   │   ├── NodeView.py       #   节点管理
│   │   │   ├── AlarmView.py      #   报警管理
│   │   │   ├── StreamView.py     #   视频流管理
│   │   │   ├── ControlView.py    #   布控管理
│   │   │   ├── OpenView.py       #   开放接口（open/*）
│   │   │   ├── StorageView.py    #   存储访问/下载
│   │   │   ├── SystemView.py     #   系统配置
│   │   │   ├── VersionView.py    #   版本检查
│   │   │   ├── InnerlView.py     #   内部回调接口
│   │   │   └── ViewsBase.py      #   公共函数/全局服务
│   │   └── utils/                # 工具类（Config/Settings/Database/
│   │                             #   ZLMediaKit/OSSystem/Upload 等）
│   ├── static/                   # 前端静态资源（Bootstrap/jQuery/
│   │                             #   Highcharts/EasyPlayer/jsencrypt）
│   ├── templates/app/            # Django 页面模板
│   ├── docker/                   # Docker 部署（MySQL + 初始化 SQL）
│   ├── tests/                    # 测试与辅助脚本
│   └── venv/                     # Python 虚拟环境
├── zlmediakit/                   # ZLMediaKit 流媒体服务器（多平台二进制）
│   ├── bin.x86.gcc9.4/           #   x86 Linux
│   ├── bin.arm.gcc9.4/           #   ARM Linux
│   └── bin.x86.windows10/        #   Windows
└── 集群管理平台对接接口.md         # 集群平台开放接口 API 文档
```

---

## 3. 核心业务功能

| 模块 | 说明 |
| --- | --- |
| **仪表盘** | 节点在线状态、在线视频流、最新报警实时展示 |
| **用户管理** | 登录/退出、图形验证码、用户增删改查、RSA 加密登录 |
| **节点管理** | 边缘节点添加/编辑/删除/同步/导入更新，状态监控（未同步/在线/掉线/版本不支持） |
| **视频流管理** | v2 壳模式：云端壳页（节点下拉 + iframe 双跳代理）内嵌边缘统一媒体源管理页，支持转发/转推代理、多协议播放（RTSP/HLS/HTTP-FLV/WS-MP4） |
| **布控管理** | v2 壳模式：内嵌边缘布控管理页，支持下发算法任务、启动/停止/复制/删除/日志查看/批量操作 |
| **报警管理** | 按分类分页：事件告警/车牌告警/人脸告警/计数告警；支持处理（已处理/误报）、审核备注、导出、深链详情；计数告警支持清零与周期历史（ECharts 趋势图 + 导出） |
| **系统配置** | 系统名称、Logo、作者信息等展示配置，日志导出 |
| **版本管理** | 对接云服务在线检查版本与更新 |
| **开放接口** | 供 Web 云平台/集群平台对接：设备发现、数据同步、流/布控管理（见 `docs/集群管理平台对接接口.md`） |
| **多语言** | 中/英双语界面一键切换（Django i18n，默认简体中文，翻译文件位于 `admin/locale/`） |

---

## 4. 数据模型

| 数据表 | 说明 | 关键字段 |
| --- | --- | --- |
| `eai_node` | 边缘节点 | `code`/`nickname`/`version`/`address`/`eai_safe`/`state`(0未同步/1在线/2掉线/3版本不支持/4读取失败) |
| `eai_node_alarm` | 节点报警 | `node_code`/`control_code`/`level`(0普通/1警告/2严重)/`risk_level`(0低/1中/2高)/`alarm_category`(0事件/1车牌/2人脸/3计数)/`state`(0未读/1未处理/2已处理/3误报/5逻辑删除)/`event_id`(推送幂等键)/`task_name`/`detect_objs`/`video_path`/`image_path` |
| `eai_node_media_source` | 节点媒体源（同步自边缘 `av_media_source`） | `node_code`/`source_code`/`source_type`(1RTSP/2RTMP/3FILE/4ONVIF/5GB28181)/`forward_state`/`online_state` |
| `eai_node_statistic_alarm` | 计数告警（边缘计数推送） | `node_code`/`control_code`/`task_name`/`count`/`enter_num`/`leave_num`/`total_num`/`reset_strategy`/`last_reset_time` |
| `eai_node_statistic_history` | 计数历史（每个清零周期归档一条） | `node_code`/`control_code`/`task_name`/`enter_num`/`leave_num`/`total_num`/`period_start`/`period_end` |
| `eai_node_stream` | 视频流 | `stream_code`/`stream_nickname`/`node_codes` |
| `eai_node_algorithm_flow` | 算法流 | `flow_code`/`flow_name`/`node_codes` |
| `eai_ai_interface` | AI 接口配置 | `code`/`address`/`api_key`/`model_name`/`state` |
| `eai_log` | 操作日志 | — |

> 存量库升级（含上述新表与新字段）见 `admin/docker/upgrade_v2.sql`；全新部署直接使用 `admin/docker/database.sql`。

---

## 5. 技术栈

| 类别 | 技术 | 说明 |
| --- | --- | --- |
| 后端框架 | Django 4.2（Python 3.8+） | Web 服务与业务 API |
| 前端 | Bootstrap 3.x / jQuery 3.x | 管理界面 |
| 可视化 | Highcharts | 仪表盘图表 |
| 播放器 | EasyPlayer | 多协议视频播放 |
| 安全 | jsencrypt / pycryptodome | 登录 RSA 加密 |
| 业务数据库 | MySQL 8.0（PyMySQL） | 业务数据 |
| 流媒体 | ZLMediaKit | 拉流/转发/转推 |
| 图像处理 | OpenCV（opencv-python） | 图片编解码/缩放 |
| 静态文件 | whitenoise | 生产环境静态资源 |
| 系统监控 | psutil | 进程/系统信息采集 |
| 国际化 | Django i18n | 中/英双语（默认 zh-hans，翻译目录 `admin/locale/`） |
| 部署 | Docker Compose | MySQL 容器化 |

依赖清单见 `admin/requirements.txt` 与 `admin/requirements-linux.txt`。

---

## 6. 端口与配置

### 6.1 端口一览

| 服务 | 端口 | 说明 |
| --- | --- | --- |
| Admin（Web/API） | `9824` | `config.json` → `adminPort` |
| ZLMediaKit RTSP | `9854` | `config.json` → `mediaRtspPort` |
| ZLMediaKit HTTP/WS | `9826` | `config.json` → `mediaHttpPort` |
| MySQL（容器映射） | `5456` | 容器内 `3306` |

### 6.2 关键配置文件

- **`admin/config.json`**：`host`、`adminPort`、`mediaRtspPort`、`mediaHttpPort`、`mediaSecret`（ZLM 密钥）、`edgeaiSafe`（集群/开放接口密钥）、`pushSecret`（报警推送签名校验密钥，留空则跳过验证）、`isEnableLoginCaptcha`（登录验证码）、`logDebug`（调试日志开关）、`install`（安装根目录）、`fontPath`、`uploadDir`、`storageDir` 等。
- **`admin/settings.json`**：系统名称、欢迎语、Logo、底部信息、作者、是否在线更新等展示配置。
- **`admin/.db.json`**：MySQL（`eaihub`）的连接信息。
- **`admin/framework/settings.py`**：Django 核心配置（数据库、会话、中间件、国际化等）。

### 6.3 鉴权机制

- **Web 页面**：基于 Session 登录；可开启图形验证码；登录密码经 RSA 加密传输。
- **集群/开放接口（`open/*`、`stream/open*`、`control/open*`）**：通过请求头 `Safe`（节点间）或 `Eai-Secret`（集群平台）鉴权，不依赖登录会话。
- **ZLMediaKit**：通过 `mediaSecret` 校验。

---

## 7. 部署与启动

### 7.1 启动数据库（Docker）

```bash
cd admin/docker
# MySQL（业务数据）
docker compose -f docker-compose.yml up -d
```

### 7.2 启动管理端（Admin）

```bash
cd admin
# 创建并激活虚拟环境（Linux）
python -m venv venv
source venv/bin/activate
pip install -r requirements-linux.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 启动服务（默认端口 9824）
python manage.py runserver 0.0.0.0:9824
```

浏览器访问 `http://<主机IP>:9824`（默认账号 `admin` / `admin`）。

### 7.3 启动流媒体服务器（ZLMediaKit）

按平台选择二进制目录，运行其中的 `eai_zlm`（配合 `config.ini`），并将 `config.json` 中 `mediaRtspPort` / `mediaHttpPort` / `mediaSecret` 与之一致。

---

## 8. 主要接口（app/urls.py）

| 分类 | 路径 | 说明 |
| --- | --- | --- |
| 主页 | `/`、`/dashboard` | 首页与仪表盘 |
| 登录 | `/login`、`/logout`、`/captcha` | 登录/退出/验证码 |
| 用户 | `/user/*` | 用户增删改查 |
| 节点 | `/node/*` | 节点管理、同步、导入更新 |
| 报警 | `/alarm/event`、`/alarm/carplate`、`/alarm/face`、`/alarm/count` | 分类告警页面（事件/车牌/人脸/计数），支持 `alarm_code` 深链开详情 |
| 计数历史 | `/alarm/count/history` | 计数周期历史页面（ECharts 趋势图） |
| 报警接口 | `/alarm/open*` | 列表/详情/处理/导出/推送入库/媒体上传/计数查询/清零/历史查询/删除/导出历史 |
| 视频流 | `/stream/*` | 流查询、转发/转推代理、播放 |
| 节点页面代理 | `/proxy/node/<node_code>/<path>` | iframe 双跳：云端登录态 + 边缘 Eai-Secret，内嵌边缘页面（`embed=1` 去整页框架） |
| 布控 | `/control/*` | 布控增删改查、启动/停止、日志（v2 壳模式内嵌边缘页面） |
| 内部 | `/inner/on_stream_not_found` | 流不存在回调 |
| 开放 | `/open/*` | 设备发现、进程/流/布控数据同步、重启 |
| 存储 | `/storage/*` | 文件下载/访问/信息 |
| 系统 | `/system/*` | 配置保存、日志导出 |
| 版本 | `/version/*` | 版本检查 |

> 集群平台对接的详细接口文档（设备发现、流代理、布控、数据同步等）见 **[`docs/集群管理平台对接接口.md`](./docs/集群管理平台对接接口.md)**。

---

## 9. 配套模块

### 9.1 zlmediakit（流媒体服务器）

- 提供 RTSP / HLS / HTTP-FLV / WS-MP4 等拉流协议，支持转发代理与转推代理。
- 提供 x86 Linux、ARM Linux、Windows 三平台二进制。

---

## 10. 相关文档

| 文档 | 说明 |
| --- | --- |
| [`admin/README.md`](./admin/README.md) | Admin 模块详细说明与开发日志 |
| [`admin/docker/DOCKER_README.md`](./admin/docker/DOCKER_README.md) | Docker 部署说明 |
| [`docs/功能清单.md`](./docs/功能清单.md) | 按侧边栏菜单梳理的界面功能清单 |
| [`docs/集群管理平台对接接口.md`](./docs/集群管理平台对接接口.md) | Web 云平台/集群平台开放接口 API 文档 |
| [`docs/节点管理接口.md`](./docs/节点管理接口.md) | 节点管理接口文档（集群平台/云平台管理端） |
| [`docs/多语言支持实施方案.md`](./docs/多语言支持实施方案.md) | 中/英双语实施方案（V1，2026-10-18） |
| [`docs/UI对齐修改方案.md`](./docs/UI对齐修改方案.md) / [`docs/UI对齐修改实施方案-V2.md`](./docs/UI对齐修改实施方案-V2.md) | 云端界面与边缘端 UI 对齐方案（V1 / V2 实施版） |
| [`docs/云端告警布控逻辑对齐方案.md`](./docs/云端告警布控逻辑对齐方案.md) / [`docs/云端告警布控逻辑对齐方案-V2.md`](./docs/云端告警布控逻辑对齐方案-V2.md) | 云端告警/布控与边缘端逻辑对齐方案（V1 / V2） |
