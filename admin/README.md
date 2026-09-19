## cloud_admin

### 简介
cloud_admin是集群管理平台（cloud_eai_server）的主管理模块，提供完整的Web界面和API服务，用于管理整个AI视频分析集群。

### 核心功能

#### 1. 系统管理
- 用户管理：用户权限、角色分配、登录认证
- 节点管理：集群节点状态监控、节点添加/删除
- 配置管理：系统配置、参数设置

#### 2. 媒体管理
- 视频流管理：实时视频流监控、流配置
- 存储管理：存储设备管理、存储策略配置

#### 3. AI功能
- 模型管理：模型版本控制、部署、性能监控
- 模型测试：测试数据集管理、性能评估、报告生成
- 模型导出：多种格式导出、打包部署

#### 4. 告警管理
- 告警配置：告警规则设置
- 告警查看：实时告警监控、历史告警查询

#### 5. 控制管理
- 设备控制：远程设备管理、控制命令下发
- 集群管理：任务调度、资源分配、负载均衡

### 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 后端框架 | Django | 3.x+ |
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