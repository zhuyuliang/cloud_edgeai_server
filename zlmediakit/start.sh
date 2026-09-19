#!/usr/bin/env bash
#
# ZLMediaKit 控制脚本（启动 / 停止 / 重启 / 状态）
#
# 用法:
#   ./start.sh start      启动流媒体服务（后台运行）
#   ./start.sh stop       停止流媒体服务
#   ./start.sh restart    重启流媒体服务
#   ./start.sh status     查看运行状态
#   ./start.sh version    查看版本
#
# 说明:
#   - 自动根据 CPU 架构选择对应的 bin 目录（x86_64 / aarch64）
#   - 必须在 zlmediakit 根目录或任意位置以 ./start.sh 方式调用
#   - PID 文件与日志文件生成在 zlmediakit 根目录下
#

set -u

# ---------------------------------------------------------------------------
# 基础路径
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 二进制目录名（按架构区分）
BIN_DIR_X86="bin.x86.gcc9.4"
BIN_DIR_ARM="bin.arm.gcc9.4"
PROC_NAME="eai_zlm"

# PID / 日志文件（位于 zlmediakit 根目录）
PID_FILE="$SCRIPT_DIR/zlm.pid"
LOG_FILE="$SCRIPT_DIR/zlm.log"

# 状态探测：HTTP API 端口（与 config.ini [http] port 一致）
HTTP_PORT=9826

# ---------------------------------------------------------------------------
# 日志输出
# ---------------------------------------------------------------------------
log_info()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO ] $*"; }
log_err()   { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $*" >&2; }

# ---------------------------------------------------------------------------
# 自动选择架构对应的 bin 目录
# ---------------------------------------------------------------------------
detect_bin_dir() {
    local arch
    arch="$(uname -m 2>/dev/null || echo 'unknown')"
    case "$arch" in
        x86_64|amd64)      echo "$SCRIPT_DIR/$BIN_DIR_X86" ;;
        aarch64|arm64)     echo "$SCRIPT_DIR/$BIN_DIR_ARM" ;;
        *)
            log_err "不支持的 CPU 架构: $arch"
            log_err "目前仅支持 x86_64 与 aarch64，如需其他架构请手动修改本脚本。"
            return 1
            ;;
    esac
}

# ---------------------------------------------------------------------------
# 检查是否已经在运行
#   返回 0 表示运行中
# ---------------------------------------------------------------------------
is_running() {
    local pid=""
    if [ -f "$PID_FILE" ]; then
        pid="$(cat "$PID_FILE" 2>/dev/null)"
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    # PID 文件失效时，回退到按进程名查找
    if pgrep -f "$PROC_NAME" >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# ---------------------------------------------------------------------------
# 获取运行中的 PID
# ---------------------------------------------------------------------------
get_pid() {
    local pid=""
    if [ -f "$PID_FILE" ]; then
        pid="$(cat "$PID_FILE" 2>/dev/null)"
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "$pid"
            return
        fi
    fi
    pgrep -f "$PROC_NAME" 2>/dev/null | head -n 1
}

# ---------------------------------------------------------------------------
# 读取 config.ini 指定段(如 http/rtsp/rtmp)中的 port / secret 值
#   用法: cfg_get <bin_dir> <段名> <键名>
# ---------------------------------------------------------------------------
cfg_get() {
    local bin_dir="$1" section="$2" key="$3"
    sed -n "/^\[$section\]/,/^\[/p" "$bin_dir/config.ini" 2>/dev/null \
        | grep -E "^$key=" | head -n 1 | cut -d= -f2 | tr -d '\r'
}

# ---------------------------------------------------------------------------
# start
# ---------------------------------------------------------------------------
do_start() {
    if is_running; then
        log_err "ZLMediaKit 已经在运行中 (PID=$(get_pid))"
        return 1
    fi

    local bin_dir
    bin_dir="$(detect_bin_dir)" || return 1

    if [ ! -f "$bin_dir/$PROC_NAME" ]; then
        log_err "未找到可执行文件: $bin_dir/$PROC_NAME"
        return 1
    fi
    if [ ! -x "$bin_dir/$PROC_NAME" ]; then
        log_err "可执行文件缺少执行权限，尝试赋予: chmod +x $bin_dir/$PROC_NAME"
        chmod +x "$bin_dir/$PROC_NAME" 2>/dev/null || true
    fi

    # 必须在 bin 目录内启动（config.ini 使用 ./www ./ffmpeg 等相对路径）
    # 同时将本地动态库目录加入 LD_LIBRARY_PATH
    cd "$bin_dir" || { log_err "无法进入目录: $bin_dir"; return 1; }

    LD_LIBRARY_PATH="$bin_dir:${LD_LIBRARY_PATH:-}" \
        nohup "./$PROC_NAME" >"$LOG_FILE" 2>&1 &
    local pid=$!

    # 短暂等待，确认进程没有立即退出
    sleep 1
    if ! kill -0 "$pid" 2>/dev/null; then
        log_err "ZLMediaKit 启动失败，请查看日志: $LOG_FILE"
        tail -n 30 "$LOG_FILE" >&2
        return 1
    fi

    echo "$pid" > "$PID_FILE"
    log_info "ZLMediaKit 已启动 (PID=$pid)"
    log_info "日志文件: $LOG_FILE"
    log_info "HTTP API : http://127.0.0.1:$HTTP_PORT/index/api/version"
    log_info "RTSP 端口: $(cfg_get "$bin_dir" rtsp port)"
    log_info "HTTP 端口: $(cfg_get "$bin_dir" http port)"
    log_info "RTMP 端口: $(cfg_get "$bin_dir" rtmp port)"
    return 0
}

# ---------------------------------------------------------------------------
# stop
# ---------------------------------------------------------------------------
do_stop() {
    if ! is_running; then
        log_info "ZLMediaKit 未在运行"
        rm -f "$PID_FILE"
        return 0
    fi

    local pid
    pid="$(get_pid)"
    log_info "正在停止 ZLMediaKit (PID=$pid) ..."
    kill "$pid" 2>/dev/null

    # 最多等待 15 秒
    for _ in $(seq 1 15); do
        if ! kill -0 "$pid" 2>/dev/null; then
            break
        fi
        sleep 1
    done

    if kill -0 "$pid" 2>/dev/null; then
        log_err "正常停止超时，强制结束 (PID=$pid)"
        kill -9 "$pid" 2>/dev/null
    fi

    rm -f "$PID_FILE"
    log_info "ZLMediaKit 已停止"
    return 0
}

# ---------------------------------------------------------------------------
# restart
# ---------------------------------------------------------------------------
do_restart() {
    do_stop
    do_start
}

# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------
do_status() {
    local pid
    pid="$(get_pid)"

    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        local bin_dir
        bin_dir="$(detect_bin_dir)"
        echo "ZLMediaKit: 运行中 (PID=$pid)"
        echo "二进制目录: $bin_dir"
        # 通过 HTTP API 探测服务是否真正就绪
        local secret code
        secret="$(cfg_get "$bin_dir" api secret)"
        code="$(curl -s -o /dev/null -w '%{http_code}' \
            "http://127.0.0.1:$HTTP_PORT/index/api/version?secret=${secret}" 2>/dev/null || echo 000)"
        if [ "$code" = "200" ]; then
            echo "API 探测 : HTTP $code (正常)"
        else
            echo "API 探测 : HTTP $code (可能未就绪或 secret 不匹配)"
        fi
        return 0
    else
        echo "ZLMediaKit: 未运行"
        return 1
    fi
}

# ---------------------------------------------------------------------------
# version
# ---------------------------------------------------------------------------
do_version() {
    local bin_dir
    bin_dir="$(detect_bin_dir)" || return 1
    echo "版本: $(cat "$bin_dir/version.txt" 2>/dev/null)"
    echo "架构: $(uname -m)"
}

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
usage() {
    echo "用法: $0 {start|stop|restart|status|version}"
    exit 1
}

ACTION="${1:-}"
case "$ACTION" in
    start)   do_start ;;
    stop)    do_stop ;;
    restart) do_restart ;;
    status)  do_status ;;
    version) do_version ;;
    *)       usage ;;
esac
