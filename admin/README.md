## cloud_admin

### 简介
cloud_admin是集群管理平台（cloud_eai_server）的主管理模块，提供完整的Web界面和API服务，用于管理整个AI视频分析集群。

### 核心功能

#### 1. 仪表盘
- 节点在线状态、在线视频流、最新报警实时展示（Highcharts 图表 + 多屏播放器）

#### 2. 用户管理
- 登录/退出、图形验证码（可开关）、用户增删改查、RSA 加密登录

#### 3. 节点管理
- 边缘节点添加/编辑/删除/同步/导入更新，状态监控（未同步/在线/掉线/版本不支持/读取失败）

#### 4. 视频流管理（v2 壳模式）
- 云端壳页（节点下拉 + iframe 双跳代理 `/proxy/node/<code>/<path>`）内嵌边缘统一媒体源管理页
- 转发/转推代理、多协议播放（RTSP / HLS / HTTP-FLV / WS-MP4）

#### 5. 布控管理（v2 壳模式）
- 内嵌边缘布控管理页，支持算法任务下发、启动/停止/复制/删除/日志查看/批量操作

#### 6. 报警管理
- 分类分页：事件告警 / 车牌告警 / 人脸告警 / 计数告警；处理（已处理/误报）、审核备注、导出、深链详情
- 计数告警：清零、周期历史（ECharts 趋势图 + 导出）

#### 7. 系统与版本
- 系统名称、Logo、作者信息等展示配置，日志导出
- 对接云服务在线检查版本与更新

#### 8. 开放接口（open/*）
- 供 Web 云平台/集群平台对接：设备发现、数据同步、流/布控管理、报警推送入库（签名校验）

#### 9. 多语言
- 中/英双语界面一键切换（Django i18n，默认简体中文，翻译文件位于 `locale/`）

### 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 后端框架 | Django | 4.2 |
| 语言 | Python | 3.8+ |
| 前端框架 | Bootstrap | 3.x |
| 前端库 | jQuery | 3.x |
| 数据库 | MySQL | 8.0 |

### 依赖环境

| 程序         | 版本               |
| ---------- |------------------|
| python     | 3.8+             |
| 依赖库      | requirements.txt / requirements-linux.txt |

### 运行方式

#### 启动服务
```bash
# 启动eai_admin服务，默认端口9824
python manage.py runserver 0.0.0.0:9824
admin admin
admin admin123
```

#### Windows 创建虚拟环境
```bash
# 创建虚拟环境
python -m venv venv

# 切换到虚拟环境
venv\Scripts\activate

# 更新pip
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装requirements
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### Linux 创建虚拟环境
```bash
# 创建虚拟环境
python -m venv venv

# 切换到虚拟环境
source venv/bin/activate

# 更新pip
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装requirements
python -m pip install -r requirements-linux.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 访问方式

打开浏览器访问：http://localhost:9824

### 问题
验证码字体过小问题：
sudo apt-get update
sudo apt-get install -y libfreetype6-dev libjpeg-dev zlib1g-dev
source venv/bin/activate
pip uninstall -y pillow
pip install --no-cache-dir pillow

### 开发日志
2026-03-10
1. 创建admin项目，登录界面
2. 首页改成google cloud menu优化，调整样式
3. 修改用户管理的样式
4. 开始节点管理的调试开发
    * 解决添加节点弹框时的蒙蔽问题
    * 调整节点管理的样式，使用bootstrap的样式
    * 