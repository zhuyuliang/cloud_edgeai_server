# 云端管理界面 UI 对齐修改方案

> 目标：参考边缘设备 Admin（`edge_ai_video_analyzer/Admin`）的最新界面，统一云端管理端（`1.cloud_eai_server/admin`）的页面风格与内容。
> 范围：**全面一致** —— 页面结构、样式、前端交互保持一致；后端视图/接口如缺失则补齐。
> 样式基准：边缘端 `web_index.html` 大屏看板卡片风格（主色 `#2a80eb`，圆角 8px 卡片，浅灰卡片头 + 主色竖条标题）。

---

## 一、两端现状对比

| 模块 | 边缘端（参考基准） | 云端（待修改） | 差距 |
| --- | --- | --- | --- |
| 首页/看板 | `web_index.html`：`dash-panel` 卡片体系、KPI 卡、主色 `#2a80eb` | `dashboard.html`：旧 gentelella 风格 | 卡片样式需整体替换 |
| 节点列表 | —（边缘端无此页） | `node/index.html`：已部分使用 Material 风格按钮/徽章 | 卡片基底与全站不统一 |
| 告警管理 | `web_alarms_event.html`：`ctrl-table` 表格体系（圆角容器、`#f5f7fa` 表头、`#2a80eb` 表头下划线、行悬停 `#f0f7ff`） | `alarm/index.html`：自带 `xc_*` 体系（主色 `#165DFF`、fancybox、自定义提示框） | 表格/按钮/弹窗/配色全替换 |
| 视频管理 | `stream/web_stream_index.html` | `stream/index.html`、`stream/player.html` | 结构样式按 web_stream_index 对齐 |
| 布控管理 | `control/index.html`、`control/add.html`：`ctrl-*` 体系 | `control/index.html`、`control/add.html`：`xc_*` 体系 | 同名页面直接对齐 |
| 公共基座 | `base_site.html`、`sidebar.html`、`top_navigation.html` | 同名文件 | 侧边栏菜单项与配色统一 |

---

## 二、全局设计规范（从边缘端提取，作为云端统一标准）

### 2.1 设计令牌（Design Tokens）
建议抽到 `static/build/css/eai-theme.css`（新增），全站引用：

```css
:root {
  --eai-primary: #2a80eb;
  --eai-success: #389e0d;
  --eai-danger:  #cf1322;
  --eai-warning: #faad14;
  --eai-border:  #e6e6e6;
  --eai-head-bg: #f5f7fa;
  --eai-row-hover: #f0f7ff;
  --eai-radius: 8px;
  --eai-shadow-sm: 0 1px 3px rgba(0,0,0,0.04);
  --eai-shadow:    0 4px 12px rgba(0,0,0,0.08);
}
```

### 2.2 卡片规范（对应需求 1：所有列表页卡片统一）
参照 `web_index.html` 的 `.dash-panel`：

- 卡片容器：白底、1px `--eai-border` 边、圆角 8px、默认 `--eai-shadow-sm`，hover 升至 `--eai-shadow`
- 卡片头：浅灰 `--eai-head-bg` 背景、底部 1px 边、标题 14px/600，标题前加 3px×14px 主色竖条
- 卡片体：`padding: 14px 16px`
- 列表页（节点/告警/视频/布控）的最外层容器统一改为此卡片，去掉各页面自有的 `xc_card`、`x_panel` 等旧卡片类

### 2.3 表格规范
参照 `web_alarms_event.html` 的 `.ctrl-table` 体系：

- 外层 `.ctrl-table-wrapper`：圆角 8px + 边框 + 阴影，横向滚动
- 表头：`#f5f7fa` 底、600 字重、底部 2px `--eai-primary` 主色线、居中
- 行：`td` 14px 垂直 padding，hover 行底色 `#f0f7ff`
- 列宽：用 `col-*` 固定列宽类（table-layout: fixed），避免各页表格错位

### 2.4 按钮/徽章/表单规范
- 主按钮：主色底、白字、圆角 4px（参考边缘端 control 页 `.ctrl-btn` / `.btn-node-primary` 二选一，建议统一为 `ctrl-btn` 体系）
- 次按钮：白底 + 灰边，hover 变浅主色底
- 状态徽章：圆角 12px 胶囊 + 前置 5px 圆点（沿用 `node/index.html` 的 `sun-state-*`，改名 `eai-badge-*` 并推广到告警/布控状态列）
- 表单控件：高度 32px、圆角 4px、边框 `#d9d9d9`，focus 主色描边

### 2.5 提示与弹窗
- 告警页自带的 `.xc-alert` 自定义提示框删除，统一用全站 toast（`static/lib/message` 或 jquery-toast）
- 图片预览：边缘端用原生弹层，云端 alarm 页引入的 fancybox 依赖评估后移除或保留二选一（建议移除，改用统一预览组件）

---

## 三、分页面修改清单

### 3.1 公共基座
| 文件 | 修改内容 |
| --- | --- |
| `templates/app/base_site.html` | 引入 `eai-theme.css`；移除各页面 `* { margin:0; font-family:... }` 这类全局重置（迁移时注意边缘端页面也有同样问题，方案中先以云端不动全局重置、仅局部规范为准） |
| `templates/app/sidebar.html` | 菜单结构与边缘端 `sidebar.html` 对齐（菜单命名/图标/顺序），云端特有菜单（节点/用户/版本）保留但样式套用同一规范 |
| `templates/app/top_navigation.html` | 统一顶栏高度、配色、用户下拉样式 |

### 3.2 首页 dashboard.html（卡片样式重点）
1. 删除旧的 `x_panel`/`x_title` 结构
2. 移植边缘端 `web_index.html` 的 `dash-panel`、`dash-panel-head/body`、`kpi-card` 结构与样式
3. 数据源沿用云端现有接口（节点在线数、告警统计等），只换皮肤，统计图表（highcharts）保留，配色改为主色系列
4. 无数据/加载态使用统一的空态组件（边缘端"无信号"占位风格）

### 3.3 节点列表 node/index.html（卡片样式重点）
1. 保留现有 Material 风格按钮/徽章中合理的部分，收敛到 2.4 规范（统一改为 `eai-` 前缀类）
2. 节点卡片列表套用 `.dash-panel` 卡片基底：卡片头显示节点名 + 状态徽章，卡片体为节点信息网格
3. 操作按钮组统一右对齐，主/次按钮按 2.4 规范

### 3.4 告警管理 alarm/index.html → 对齐 `web_alarms_event.html`
1. 删除 `:root --xc-*` 变量与 `xc_*` 样式块，改用 2.1~2.4 规范
2. 表格结构替换为 `.ctrl-table-wrapper` + `.ctrl-table`，列定义参考事件告警页：勾选 / 快照 / 任务 / 摄像头（云端为"节点+通道"）/ 风险等级 / 时间 / 操作
3. 筛选工具栏（时间范围、类型、节点）改用统一样式的 `daterangepicker` + 表单控件
4. 快照预览弹层：移除 fancybox，改为统一预览组件
5. 批量操作（确认/删除）按钮组与布控页一致
6. 视图层：核对 `views/AlarmView.py` 接口返回字段是否满足新表格所需（缺字段则补，保持与边缘端事件告警接口字段命名风格一致）

### 3.5 视频管理 stream/index.html、player.html → 对齐 `web_stream_index.html`
1. 列表页卡片化：每路流一张卡片（封面/状态/操作），套用 `.dash-panel`
2. 工具栏、搜索、分页组件统一
3. `player.html` 播放器页：保留 easyPlayer/webrtc 播放逻辑，外壳样式（标题栏、信息区、按钮）与边缘端 player 页一致
4. 视图层：`views/StreamView.py` 补齐新页面所需的流状态字段（在线/离线、快照地址）

### 3.6 布控管理 control/index.html、add.html → 与边缘端同名页面对齐
1. 以边缘端 `control/index.html` / `add.html` 为基准，逐段替换云端的 `xc_*` 实现
2. 列表：`ctrl-table` 体系，列：勾选 / 布控名称 / 关联节点通道 / 算法 / 时间段 / 状态 / 操作
3. 新增/编辑页 `add.html`：分步/分区表单样式、算法参数区、时间选择器与边缘端一致
4. 视图层：`views/ControlView.py` 与边缘端布控接口字段对齐（云端需额外带节点维度，节点字段附加在每条布控记录上）

### 3.7 其余页面（user / system / version / storage）
- 不做内容对齐（边缘端无对应页），但卡片、表格、按钮全部套用第二章规范，保证全站风格统一

---

## 四、实施步骤（建议按顺序执行，每步可独立验收）

| 步骤 | 内容 | 影响面 | 预计工作量 |
| --- | --- | --- | --- |
| 1 | 新建 `eai-theme.css` 设计令牌 + 卡片/表格/按钮公共类 | 新增文件，无风险 | 0.5 天 |
| 2 | `base_site.html` / `sidebar.html` / `top_navigation.html` 基座统一 | 全站 | 0.5 天 |
| 3 | `dashboard.html` 看板卡片化 | 单页 | 0.5 天 |
| 4 | `node/index.html` 列表卡片收敛 | 单页 | 0.5 天 |
| 5 | `alarm/index.html` 对齐事件告警页（含 AlarmView 字段核对） | 页面+视图 | 1 天 |
| 6 | `stream/index.html` + `player.html` 对齐视频管理 | 页面+视图 | 1 天 |
| 7 | `control/index.html` + `add.html` 对齐布控管理 | 页面+视图 | 1 天 |
| 8 | user/system/version/storage 页面套公共规范 | 多页 | 0.5 天 |
| 9 | 全站回归：配色/间距/响应式/弹窗/空态检查 | 全站 | 0.5 天 |

---

## 五、注意事项与风险

1. **全局重置问题**：两端页面都存在 `* { margin:0; padding:0; ... }` 内联重置，逐页删除时需在基座统一补上盒模型规则，避免删除后布局塌陷。
2. **依赖清理**：alarm 页的 fancybox、各 `xc_*` 页面重复定义的变量，替换后需清理 `{% block stylesheets %}` 中的冗余引用。
3. **接口差异**：云端比边缘端多"节点"维度（一个云端管多个边缘节点），对齐字段时告警/视频/布控记录都需要保留节点标识，不可直接照抄边缘端接口结构。
4. **不改动后端业务逻辑**：除补充缺失字段外，不改已有接口行为；所有改动以模板 + 静态资源为主。
5. **验收标准**：任一页面截图与边缘端对应页并排对比，卡片、表格、按钮风格目测一致；浏览器 1366/1920 宽度下无横向异常滚动。
