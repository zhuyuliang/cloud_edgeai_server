# ZLMediaKit 流媒体服务 - 启动说明

本项目基于 ZLMediaKit（版本：`ZLMediaKit(2025/05/11 master)`）定制编译，用于提供
视频流的接入、转码与分发能力，与 `admin`（云端管理平台）配合使用。

---

## 1. 目录结构

```
zlmediakit/
├── start.sh                  # 启动/停止/重启/状态 控制脚本（推荐）
├── zlm.log                   # 运行日志（脚本生成）
├── zlm.pid                   # PID 文件（脚本生成）
├── bin.x86.gcc9.4/           # x86_64 (amd64) Linux 版本
│   ├── eai_zlm               # 主程序
│   ├── config.ini            # 配置文件
│   ├── libcrypto.so.1.1      # 本地动态库（openssl）
│   ├── libsrtp2.so.1         # 本地动态库（srtp）
│   ├── libssl.so.1.1         # 本地动态库（openssl）
│   └── version.txt           # 版本信息
├── bin.arm.gcc9.4/           # ARM64 (aarch64) Linux 版本
│   └── ...（同上）
└── bin.x86.windows10/        # Windows 版本（仅配置样例，无程序）
```

> 说明：运行目录中的 `www/`、`ffmpeg/`、`snap/` 等目录由程序首次启动时自动创建
> （对应 `config.ini` 中的相对路径）。

---

## 2. 前置条件

- 操作系统：Linux（x86_64 或 aarch64）
- 动态库：`eai_zlm` 依赖的 `libcrypto.so.1.1` / `libsrtp2.so.1` / `libssl.so.1.1`
  均随包提供，**无需**在系统中额外安装，但启动时必须通过
  `LD_LIBRARY_PATH` 指向程序所在目录（见下文脚本/手动命令）。
- 端口：需确保以下端口未被占用（默认值，见 `config.ini`）：

| 端口 | 用途                 | 对应 admin 配置项   |
| ---- | -------------------- | ------------------- |
| 9826 | HTTP API / HLS / FLV | `mediaHttpPort`     |
| 9854 | RTSP 拉流/推流       | `mediaRtspPort`     |
| 9835 | RTMP 推流/拉流       | -                   |

---

## 3. 快速启动（推荐）

```bash
cd zlmediakit/

# 启动（后台运行）
./start.sh start

# 查看状态
./start.sh status

# 重启
./start.sh restart

# 停止
./start.sh stop

# 查看版本
./start.sh version
```

脚本会自动根据 CPU 架构（`uname -m`）选择 `bin.x86.gcc9.4` 或 `bin.arm.gcc9.4`，
PID 与日志分别写入 `zlmediakit/zlm.pid`、`zlmediakit/zlm.log`。

> 首次使用如提示无执行权限，请先执行：
> `chmod +x start.sh bin.x86.gcc9.4/eai_zlm bin.arm.gcc9.4/eai_zlm`

---

## 4. 手动启动方式

### 4.1 前台运行（便于调试，Ctrl+C 退出）

```bash
cd zlmediakit/bin.x86.gcc9.4
LD_LIBRARY_PATH=. ./eai_zlm
```

### 4.2 后台运行

```bash
cd zlmediakit/bin.x86.gcc9.4
LD_LIBRARY_PATH=. nohup ./eai_zlm > zlm.log 2>&1 &
echo $! > zlm.pid
```

### 4.3 停止

```bash
kill $(cat zlm.pid)        # 优雅停止
# 如无法停止，强制结束：
# kill -9 $(cat zlm.pid)
```

> **重要**：必须在 `bin.*/` 目录内启动（`cd` 进入该目录），因为 `config.ini`
> 中的 `./www`、`./ffmpeg`、`./snap` 等均为相对路径；且必须设置
> `LD_LIBRARY_PATH=.` 或 `LD_LIBRARY_PATH=/绝对路径/bin.x86.gcc9.4`。

---

## 5. systemd 服务方式（可选，推荐生产环境）

创建服务文件 `/etc/systemd/system/zlmediakit.service`：

```ini
[Unit]
Description=ZLMediaKit Streaming Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/steve/project/edge_ai/1.cloud_eai_server/zlmediakit/bin.x86.gcc9.4
Environment=LD_LIBRARY_PATH=/home/steve/project/edge_ai/1.cloud_eai_server/zlmediakit/bin.x86.gcc9.4
ExecStart=/home/steve/project/edge_ai/1.cloud_eai_server/zlmediakit/bin.x86.gcc9.4/eai_zlm
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

启用并启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now zlmediakit
sudo systemctl status zlmediakit
```

---

## 6. 与 admin 平台对接

`admin` 通过 `admin/config.json` 中的配置访问 ZLMediaKit：

```json
{
    "mediaRtspPort": 9854,
    "mediaHttpPort": 9826,
    "mediaSecret": "请替换为与config.ini一致的强随机secret"
}
```

- `mediaHttpPort` / `mediaRtspPort` 必须与 `config.ini` 中 `[http] port` / `[rtsp] port` 一致。
- `mediaSecret` 必须与 `config.ini` 中 `[api] secret` **完全一致**，否则 admin
  无法调用流媒体 API（如在线状态、流列表等）。
- `config.ini` 中 `[hook] on_stream_not_found` 默认指向
  `http://127.0.0.1:9824/inner/on_stream_not_found`，用于向 admin 上报未找到的流，
  需保证 `admin`（端口 9824）已启动且可访问。

**版本对应关系（默认）**：

| 项                  | config.ini        | admin/config.json |
| ------------------- | ----------------- | ----------------- |
| HTTP API 端口       | `[http] port=9826`    | `mediaHttpPort=9826`    |
| RTSP 端口           | `[rtsp] port=9854`    | `mediaRtspPort=9854`    |
| 安全校验 secret     | `[api] secret=请替换为与config.ini一致的强随机secret` | `mediaSecret=请替换为与config.ini一致的强随机secret` |

> ⚠️ **注意**：当前仓库中 `config.ini` 的 `[api] secret` 与 `admin/config.json`
> 的 `mediaSecret` **不一致**（分别为 `请替换为与config.ini一致的强随机secret` 与
> `请替换为与config.ini一致的强随机secret`）。部署前请将两处统一为同一个值，否则 admin 中
> 流媒体状态显示离线/流列表获取失败。

---

## 7. 验证服务是否正常

```bash
# 1) 进程是否存活
pgrep -f eai_zlm

# 2) HTTP API 是否就绪（secret 需替换为 config.ini 中实际值）
curl "http://127.0.0.1:9826/index/api/version?secret=你的secret"
# 期望返回: {"code":0,"data":{"version":"..."},"msg":"success"}

# 3) 查看端口监听
ss -tlnp | grep -E '9826|9854|9835'
```

---

## 8. 常见问题（FAQ）

### 8.1 启动提示动态库 not found（libsrtp2 / libssl / libcrypto）
未设置 `LD_LIBRARY_PATH` 所致。请使用 `./start.sh start`，或手动启动时加上
`LD_LIBRARY_PATH=.`（见第 4 节）。

### 8.2 admin 中显示流媒体离线，但进程已启动
多为 `[api] secret` 与 `admin/config.json` 的 `mediaSecret` 不一致导致，请统一
两处 secret（见第 6 节）。

### 8.3 端口被占用
```bash
ss -tlnp | grep 9826
# 释放占用后重启，或修改 config.ini 中 [http]/[rtsp]/[rtmp] 的 port，
# 并同步修改 admin/config.json 中的 mediaHttpPort / mediaRtspPort。
```

### 8.4 开机自启
推荐使用 systemd（第 5 节）。也可在 `/etc/rc.local` 中添加：
`cd /home/steve/project/edge_ai/1.cloud_eai_server/zlmediakit && ./start.sh start`
