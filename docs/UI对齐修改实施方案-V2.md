# 云端管理界面 UI 对齐修改方案 V2（实施版）

> 本版基于 V1（`UI对齐修改方案.md`）审查修订，已对照两端实际代码核实，并确认以下决策：
> 1. 首页"控制面板"= `index.html` 是看板对齐目标页；`dashboard.html` 是多屏播放器，只换外壳样式
> 2. 视频/布控**维持 v2 iframe 代理架构**（云端壳 + 嵌入边缘页面），只统一壳页样式，不做本地重实现
> 3. 告警页**换皮不动逻辑**：保留详情弹窗、深链、导出等全部交互，只替换样式体系
>
> 样式基准：边缘端 `web_index.html` 大屏看板卡片风格（主色 `#2a80eb`，圆角 8px 卡片，浅灰卡片头 + 主色竖条标题）。

---

## 一、V1 方案问题清单（已修正）

| # | V1 描述 | 实际情况 | V2 修正 |
| --- | --- | --- | --- |
| 1 | `dashboard.html` 是旧看板，需卡片化 | `dashboard.html` 是多屏播放器（1/4/9/16 分屏 easyPlayer，路由 `/dashboard`，侧边栏无入口）；真正的控制面板是 `/` → `index.html`（gentelella `x_panel` + highcharts） | 看板目标页改为 `index.html`；`dashboard.html` 仅外壳规范化 |
| 2 | 视频/布控页逐段替换为边缘同名页面 | `StreamView.index` 渲染 `stream/index_v2.html`、`ControlView.index/add/edit` 渲染 `control/index_v2.html` / `control/iframe.html`（v2 iframe 代理模式，iframe 内即边缘最新 UI）；旧 `stream/index.html`、`control/index.html`、`control/add.html` 是不再被引用的死模板 | 维持 v2 架构，仅改 3 个壳页样式；死模板在最后一步清理 |
| 3 | 告警页为 `alarm/index.html`，需移除 fancybox | 实际为 `alarm/list.html`（事件/车牌/人脸共用）+ `count.html` + `count_history.html` 共 3 页；无 fancybox，用的是自定义 `xc_modal` 详情弹窗（含视频/图片/处理表单/`?alarm_code=` 深链）；fancybox 在 `dashboard.html` | 目标文件更正为 3 页；策略改为"换皮不动逻辑"，`xc_modal` 保留但样式规范化 |
| 4 | 涉及 storage 页面 | 不存在 storage 模板页（仅 `storage/access` 文件接口） | 从清单移除 |
| 5 | 未提 login/message/count 等页 | `user/login.html`、`message.html`、`alarm/count.html`、`count_history.html` 均存在 | 补入第 7 步统一规范 |
| 6 | 徽章 `sun-state-*` 直接改名推广 | 告警状态语义（6 种）与节点在线状态不同 | `eai-badge-*` 按语义建修饰类（success/error/warning/info/default），不同业务挂不同修饰类 |

另发现两个与 UI 方案无关的现存问题，建议单独记 issue：
- `NodeView.add` / `UserView.add` 引用的 `node/add.html`、`user/add.html` 模板不存在（GET 会 TemplateDoesNotExist；若添加功能实为 index 页内弹窗则属死路由）
- 云端 `getSnapByFFmpeg` 因缺 `ffmpeg` 报错返回空；`/control/null` 404 为 iframe 代理跳转泄漏变种

---

## 二、全局设计规范（不变，摘自 V1）

### 2.1 设计令牌 → `static/build/css/eai-theme.css`（新增）

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

### 2.2 公共类（从边缘端提取到 eai-theme.css，全站引用）
- `.dash-panel` / `.dash-panel-head` / `.dash-panel-body`（源：`web_index.html`）——所有列表页最外层容器
- `.kpi-card` 及 `kpi-danger/warning/success/info/default/purple` 修饰（源：`web_index.html`）
- `.ctrl-table-wrapper` / `.ctrl-table` / `col-*` 固定列宽（源：`web_alarms_event.html`）
- `.ctrl-btn` 主/次按钮（源：边缘 control 页）
- `.eai-badge-*` 胶囊状态徽章（源：`node/index.html` 的 `sun-state-*` 改名，按语义扩展修饰类）
- 表单控件：高 32px、圆角 4px、边框 `#d9d9d9`、focus 主色描边

### 2.3 提示与弹窗
- 各页 `.xc-alert` 自定义 toast 删除，统一换全站 toast（`static/lib/message`）
- 告警 `xc_modal` 保留结构与逻辑，样式套用统一弹窗规范（白底圆角 8px、标题栏、遮罩）

---

## 三、分页面修改清单（修订版）

| 步骤 | 文件 | 修改内容 | 工作量 |
| --- | --- | --- | --- |
| 1 | `static/build/css/eai-theme.css`（新增） | 设计令牌 + 第二章公共类 | 0.5 天 |
| 2 | `base_site.html` / `sidebar.html` / `top_navigation.html` | 引入主题 CSS；侧边栏配色/结构与边缘对齐（云端特有菜单保留）；顶栏高度/配色/用户下拉统一 | 0.5 天 |
| 3 | `index.html`（控制面板） | 删 `x_panel`/`x_title`，移植 `dash-panel` + `kpi-card`；数据源沿用现有接口；highcharts 保留换主色系列；统一空态 | 1 天 |
| 4 | `node/index.html` | 卡片化套 `dash-panel`（卡片头=节点名+状态徽章，卡片体=信息网格）；`sun-state-*`→`eai-badge-*`、`btn-node-*`→`ctrl-btn`；操作按钮右对齐 | 0.5 天 |
| 5 | `alarm/list.html`、`alarm/count.html`、`alarm/count_history.html` | **换皮不动逻辑**：`xc_container`→`dash-panel`、表格→`ctrl-table`、`xc-alert`→全站 toast、`xc_modal` 样式规范化；保留深链/导出/ECharts；无后端改动 | 1 天 |
| 6 | `stream/index_v2.html`、`control/index_v2.html`、`control/iframe.html` | v2 壳页套卡片规范（`xc_container`/`xc_btn_primary` → 主题类）；**不动 iframe 代理逻辑** | 0.25 天 |
| 7 | `user/index.html`、`user/login.html`、`system/settings.html`、`version/index.html`、`message.html` | 套公共规范（卡片/表格/按钮/表单） | 0.5 天 |
| 8 | `dashboard.html`（多屏播放器） | 只换外壳：侧栏/控制按钮/配色统一，easyPlayer 与分屏逻辑不动 | 0.25 天 |
| 9 | 死模板清理 + 全站回归 | 删除旧 `stream/index.html`、`control/index.html`、`control/add.html`（删前全局确认无引用）；1366/1920 宽度回归、弹窗/空态/深链检查 | 0.5 天 |

依赖关系：1 → 2 → (3/4/5/6/7/8 可并行) → 9。总计约 5 天。

---

## 四、注意事项与风险

1. **全局重置**：两端页面均有 `* { margin:0 }` 内联重置，迁移时先在 eai-theme.css 补盒模型规则，再逐页删除，防布局塌陷。
2. **v2 壳页宽度**：壳页容器必须 `width:100%`（父级 `.main_content_wrapper` 是 flex 列容器，`margin:0 auto` 会收缩）。
3. **接口差异**：云端多"节点"维度，告警/视频/布控记录保留节点标识，不照抄边缘接口结构。本方案不改后端业务逻辑。
4. **iframe 内页面不动**：视频/布控 iframe 内是边缘端页面（边缘 UI），云端只管壳。
5. **验收标准**：任一页面与边缘端对应页并排对比风格目测一致；1366/1920 无横向异常滚动；告警深链 `?alarm_code=`、详情处理、导出、计数历史图表功能回归通过。
