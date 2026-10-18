from app.views.ViewsBase import *
from app.models import *
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _
def index(request):
    context = {
        "settings": f_settingsReadData()
    }
    params = f_parseGetParams(request)

    node_code = params.get("node_code","").strip()
    nodes = g_database.select("select code,nickname from eai_node where state=1 order by id desc")
    # 填充默认选中的节点start
    if node_code == "":
        if len(nodes) > 0:
            node_code = nodes[0]["code"]
    # 填充默认选中的节点end
    context["node_code"] = node_code
    context["nodes"] = nodes

    # 新版：iframe 双跳嵌入边缘统一媒体源管理页（proxy/node/<code>/stream/index?embed=1）
    return render(request, 'app/stream/index_v2.html', context)

def api_openIndex(request):
    ret = False
    msg = _("未知错误")
    data = []
    pageData = []
    extra = {}

    if request.method == 'GET':
        params = f_parseGetParams(request)
        # g_logger.info("StreamView.getIndex() params:%s" % str(params))

        page = params.get('p', 1)
        page_size = params.get('ps', 10)
        search_text = str(params.get('search_text', "")).strip()
        node_code = str(params.get('node_code', "")).strip()

        __node_ret, __node_msg, node = f_checkNode(node_code=node_code)
        if __node_ret:
            try:
                page = int(page)
            except:
                page = 1
            try:
                page_size = int(page_size)
                if page_size < 1:
                    page_size = 1
            except:
                page_size = 10

            try:

                headers = {
                    "User-Agent": PROJECT_UA,
                    "Content-Type": "application/json;",
                    "Eai-Secret": node.eai_safe
                }
                res = requests.get(url='%s/stream/openIndex?p=%s&ps=%s&search_text=%s' % (node.address, page, page_size, search_text),
                                   headers=headers, timeout=TIMEOUT)

                if res.status_code == 200:
                    res_result = res.json()
                    msg = res_result.get("msg")
                    if int(res_result.get("code", 0)) == 1000:
                        data = res_result.get("data")
                        pageData = res_result.get("pageData")
                        extra = res_result.get("extra")

                        ret = True
                else:
                    raise Exception("status=%d" % res.status_code)
            except Exception as e:
                msg = str(e)
        else:
            msg = __node_msg
    else:
        msg = "request method not supported"
    res = {
        "code": 1000 if ret else 0,
        "msg": msg,
        "data": data,
        "pageData": pageData,
        "extra": extra
    }
    # g_logger.info("StreamView.getIndex() res:%s" % str(res))
    return f_responseJson(res)

def api_openAddStreamProxy(request):
    ret = False
    msg = _("未知错误")
    if request.method == 'POST':
        __check_ret, __check_msg = f_checkRequestSafe(request)
        if __check_ret:
            params = f_parsePostParams(request)
            g_logger.info("StreamView.openAddStreamProxy() params:%s" % str(params))

            node_code = str(params.get('node_code', "")).strip()
            __node_ret, __node_msg, node = f_checkNode(node_code=node_code)
            if __node_ret:
                try:

                    headers = {
                        "User-Agent": PROJECT_UA,
                        "Content-Type": "application/json;",
                        "Eai-Secret": node.eai_safe
                    }
                    res = requests.post(url='%s/stream/openAddStreamProxy' % node.address,
                                        headers=headers, data=json.dumps(params), timeout=TIMEOUT)

                    if res.status_code == 200:
                        res_result = res.json()
                        msg = res_result.get("msg")
                        if int(res_result.get("code", 0)) == 1000:
                            ret = True

                    else:
                        raise Exception("status=%d" % res.status_code)
                except Exception as e:
                    msg = str(e)
            else:
                msg = __node_msg
        else:
            msg = __check_msg
    else:
        msg = "request method not supported"

    res = {
        "code": 1000 if ret else 0,
        "msg": msg
    }
    g_logger.info("StreamView.openAddStreamProxy() res:%s" % str(res))
    return f_responseJson(res)

def api_openDelStreamProxy(request):
    ret = False
    msg = _("未知错误")
    if request.method == 'POST':
        params = f_parsePostParams(request)
        g_logger.info("StreamView.openDelStreamProxy() params:%s" % str(params))

        node_code = str(params.get('node_code', "")).strip()
        __node_ret, __node_msg, node = f_checkNode(node_code=node_code)
        if __node_ret:
            try:

                headers = {
                    "User-Agent": PROJECT_UA,
                    "Content-Type": "application/json;",
                    "Eai-Secret": node.eai_safe
                }
                res = requests.post(url='%s/stream/openDelStreamProxy' % node.address,
                                    headers=headers, data=json.dumps(params), timeout=TIMEOUT)

                if res.status_code == 200:
                    res_result = res.json()
                    msg = res_result.get("msg")
                    if int(res_result.get("code", 0)) == 1000:
                        ret = True

                else:
                    raise Exception("status=%d" % res.status_code)
            except Exception as e:
                msg = str(e)
        else:
            msg = __node_msg
    else:
        msg = "request method not supported"

    res = {
        "code": 1000 if ret else 0,
        "msg": msg
    }
    g_logger.info("StreamView.openDelStreamProxy() res:%s" % str(res))
    return f_responseJson(res)
def api_openHandleAllStreamProxy(request):
    ret = False
    msg = _("未知错误")

    if request.method == 'POST':
        __check_ret, __check_msg = f_checkRequestSafe(request)
        if __check_ret:
            params = f_parsePostParams(request)
            g_logger.info("StreamView.openHandleAllStreamProxy() params:%s" % str(params))

            node_code = str(params.get('node_code', "")).strip()
            __node_ret, __node_msg, node = f_checkNode(node_code=node_code)
            if __node_ret:
                try:
                    if node.version < 2:
                        raise Exception(
                            _("v3系列节点不支持该功能"))

                    headers = {
                        "User-Agent": PROJECT_UA,
                        "Content-Type": "application/json;",
                        "Eai-Secret": node.eai_safe
                    }
                    res = requests.post(url='%s/stream/openHandleAllStreamProxy' % node.address,
                                        headers=headers, data=json.dumps(params), timeout=TIMEOUT)

                    if res.status_code == 200:
                        res_result = res.json()
                        msg = res_result.get("msg")
                        if int(res_result.get("code", 0)) == 1000:
                            ret = True
                    else:
                        raise Exception("status=%d" % res.status_code)
                except Exception as e:
                    msg = str(e)
            else:
                msg = __node_msg
        else:
            msg = __check_msg
    else:
        msg = "request method not supported"

    res = {
        "code": 1000 if ret else 0,
        "msg": msg
    }
    g_logger.info("StreamView.openHandleAllStreamProxy() res:%s" % str(res))
    return f_responseJson(res)
def api_openDel(request):
    ret = False
    msg = _("未知错误")
    if request.method == 'POST':
        __check_ret, __check_msg = f_checkRequestSafe(request)
        if __check_ret:
            params = f_parsePostParams(request)
            g_logger.info("StreamView.openDel() params:%s" % str(params))

            node_code = str(params.get('node_code', "")).strip()
            __node_ret, __node_msg, node = f_checkNode(node_code=node_code)
            if __node_ret:
                try:
                    headers = {
                        "User-Agent": PROJECT_UA,
                        "Content-Type": "application/json;",
                        "Eai-Secret": node.eai_safe
                    }
                    res = requests.post(url='%s/stream/openDel' % node.address,
                                        headers=headers, data=json.dumps(params), timeout=TIMEOUT)

                    if res.status_code == 200:
                        res_result = res.json()
                        msg = res_result.get("msg")
                        if int(res_result.get("code", 0)) == 1000:
                            ret = True

                    else:
                        raise Exception("status=%d" % res.status_code)
                except Exception as e:
                    msg = str(e)
            else:
                msg = __node_msg
        else:
            msg = __check_msg
    else:
        msg = "request method not supported"

    res = {
        "code": 1000 if ret else 0,
        "msg": msg
    }
    g_logger.info("StreamView.openDel() res:%s" % str(res))
    return f_responseJson(res)
def player(request):
    context = {
        "settings": f_settingsReadData()
    }
    params = f_parseGetParams(request)
    g_logger.debug("StreamView.player() params:%s" % str(params))

    stream_app = params.get('app', "").strip()
    stream_name = params.get('name', "").strip()
    node_code = params.get('node_code', "").strip()

    __node_ret, __node_msg, node = f_checkNode(node_code=node_code)
    if stream_app and  stream_name and __node_ret:
        app = node_code
        name = "%s-%s"%(stream_app,stream_name)
        info = {
            "node_code": node_code,
            "stream_app":stream_app,
            "stream_name":stream_name,
            "wsHost":g_zlm.get_wsHost(),
            "wsMp4Url":g_zlm.get_wsMp4Url(app=app, name=name),
            "httpMp4Url":g_zlm.get_httpMp4Url(app=app, name=name),
            "rtspUrl":g_zlm.get_rtspUrl(app=app, name=name)
        }
        context["info"] = info
        g_logger.debug("StreamView.player() info:%s" % str(info))

    # 无流参数（如从侧边栏"单屏播放器"直接进入）时也停留在本页，支持手动输入地址播放，
    # 不再跳转回视频管理页
    return render(request, 'app/stream/player.html', context)


# ============================================================================
# 节点页面代理（iframe 双跳模式）
# 云端登录用户 -> 云端代理(附 Eai-Secret) -> 边缘页面(?embed=1)
# ============================================================================
import re as _re
from django.http import HttpResponse as _HttpResponse

# 允许代理转发的边缘路径（页面 + 页面内 AJAX + 静态资源）
NODE_PROXY_PATH_PREFIXES = (
    # 视频管理页及其依赖
    "stream/index", "stream/source/", "stream/player", "stream/downloadVideo",
    "stream/downloadFile", "system/gb28181/", "api/getControls",
    # 布控跳转页（P1 仅代理直跳；P2 布控模块完整改造）
    "controls", "control/add", "control/edit",
    "api/getSnap", "api/getControlJsonFile", "api/vllm/",
    "api/postAddAnalyzer", "api/postCancelAnalyzer",
    "api/postAddControl", "api/postEditControl", "api/postDelControl",
    "stream/getStreamwsMp4Url",
    # 静态资源
    "static/",
)

# 边缘页面返回 JSON 中需要重写为云端代理地址的前缀
NODE_PROXY_JSON_REWRITE_KEYS = ("download_url",)


def _proxyRewriteStreamUrl(res_json, node_code, path):
    """布控/视频页内 AJAX 返回的播放地址重写为云端 ZLM 地址。

    边缘 stream/getStreamwsMp4Url 返回边缘 ZLM 的 ws/mp4 绝对地址，
    浏览器在 iframe 代理模式下无法直达边缘 ZLM。云端 ZLM 通过
    inner/on_stream_not_found hook 按需从边缘拉流，故统一重写为
    云端地址：app=<node_code>，name=<边缘app>-<边缘name>。
    仅处理 GET/POST 参数中带 app+name 的场景（边缘接口要求必传）。
    """
    if path != "stream/getStreamwsMp4Url":
        return None
    data = res_json.get("data")
    if not isinstance(data, dict):
        return None
    app = data.get("app") or data.get("stream_app")
    name = data.get("name") or data.get("stream_name")
    if not (app and name):
        # 边缘返回结构含 app/name 字段则重写；否则保守不处理
        has_url = data.get("wsMp4Url") or data.get("wsHost")
        if not has_url:
            return None
        app, name = None, None
    new_name = "%s-%s" % (app, name) if (app and name) else None
    if new_name:
        data["wsMp4Url"] = g_zlm.get_wsMp4Url(app=node_code, name=new_name)
        data["httpMp4Url"] = g_zlm.get_httpMp4Url(app=node_code, name=new_name)
        data["rtspUrl"] = g_zlm.get_rtspUrl(app=node_code, name=new_name)
        data["wsHost"] = g_zlm.get_wsHost()
        # 预留：边缘旧版可能返回 flv 字段
        if data.get("httpFlvUrl"):
            data["httpFlvUrl"] = g_zlm.get_httpFlvUrl(app=node_code, name=new_name)
        return True
    return None


def _proxyHtmlRewrite(html_text, node_code):
    """将边缘 HTML 中的绝对路径重写为云端代理路径"""
    # 注入覆写脚本（置于 head 顶部，先于页面脚本执行）：
    # 1) window.open('/stream/player?...') → 云端播放器并追加 node_code
    #    （云端 ZLM 经 inner/on_stream_not_found 拉边缘流，浏览器无法直连边缘 ZLM）
    # 2) window.open('/xxx') 其它绝对路径 → 加代理前缀（兼容字符串拼接写法）
    inject_script = (
        "<script>(function(){var CODE=%s;var _open=window.open.bind(window);"
        "window.open=function(u,n,f){try{if(typeof u==='string'&&u.charAt(0)==='/'){"
        "if(u.indexOf('/stream/player')===0){u+=(u.indexOf('?')>=0?'&':'?')+'node_code='+CODE;}"
        "else{u='/proxy/node/'+CODE+u;}}}catch(e){}return _open(u,n,f);};})();</script>"
    ) % json.dumps(node_code)
    html_text = html_text.replace("<head>", "<head>" + inject_script, 1)

    # href="/xxx" src="/xxx" action="/xxx" → /proxy/node/<code>/xxx
    # （对字符串拼接写法同样安全：仅重写字面量开头部分）
    html_text = _re.sub(
        r'(href|src|action)=(["\'])/(?!/)',
        lambda m: "%s=%s/proxy/node/%s/" % (m.group(1), m.group(2), node_code),
        html_text)
    html_text = _re.sub(
        r'url\((["\'])/(?!/)',
        lambda m: "url(%s/proxy/node/%s/" % (m.group(1), node_code),
        html_text)
    # JS 页面跳转 window.location.href = '/xxx'（window.open 已由注入脚本覆写处理）
    html_text = _re.sub(
        r"window\.location\.href *= *['\"]/(?!/)",
        lambda m: "window.location.href = '/proxy/node/%s/" % node_code,
        html_text)
    # AJAX url: '/xxx'（含 url:'/xxx' 与 url: '/xxx'）
    html_text = _re.sub(
        r"url: *['\"]/(?!/)",
        lambda m: "url: '/proxy/node/%s/" % node_code,
        html_text)

    # 布控列表页运行时 JS 构造的跳转字面量（上面的属性/location 正则覆盖不到）：
    #   1) var addUrl = "/control/add"（变量赋值后再 window.location.href = addUrl）
    #   2) item_html += "<a href=\"/control/edit?code=..."（JS 字符串拼接的 href，
    #      引号前带转义符，属性正则无法命中）
    # 若不加代理前缀，iframe 内会跳到云端 /control/* 路由，云端再渲染整壳页面
    # （含侧边栏/顶栏/内层 iframe），造成页面层层叠加、无法进入表单页。
    # 注：模式要求引号紧邻 /control/，已重写为 /proxy/node/... 的 URL 天然不会命中（幂等）。
    html_text = _re.sub(
        r"(['\"])/control/(add|edit)\b",
        lambda m: "%s/proxy/node/%s/control/%s" % (m.group(1), node_code, m.group(2)),
        html_text)

    # 播放地址重写：边缘 ZLM 的 ws-mp4 / http-flv 绝对地址 → 云端 ZLM 地址
    # （云端经 inner/on_stream_not_found 按需拉边缘流：app=<node_code>，
    #   name=<边缘app>-<边缘name>；覆盖布控表单 streamCodeDict 等字面量注入场景）
    def _m_url(m):
        proto, app, name, fmt = m.group(1), m.group(2), m.group(3), m.group(4)
        new_name = "%s-%s" % (app, name)
        if fmt == "mp4" and proto == "ws":
            return g_zlm.get_wsMp4Url(app=node_code, name=new_name)
        if fmt == "mp4":
            return g_zlm.get_httpMp4Url(app=node_code, name=new_name)
        if proto == "ws":
            return g_zlm.get_wsFlvUrl(app=node_code, name=new_name)
        return g_zlm.get_httpFlvUrl(app=node_code, name=new_name)
    html_text = _re.sub(
        r"(ws|http)://[^\"'\s<>]+/([A-Za-z0-9_\-]+)/([A-Za-z0-9_\-]+)\.live\.(mp4|flv)",
        _m_url,
        html_text)
    return html_text


def _proxyForward(request, node, path, method_override=None, get_params=None):
    """将请求转发到边缘节点，返回 (requests.Response, err_msg)"""
    url = "%s/%s" % (node.address.rstrip('/'), path)
    headers = {
        "User-Agent": PROJECT_UA,
        "Eai-Secret": node.eai_safe,
    }
    # 转发查询串（支持注入参数，如 embed=1）
    query_dict = get_params if get_params is not None else request.GET
    if query_dict:
        from urllib.parse import urlencode
        if hasattr(query_dict, "dict"):
            q = urlencode(query_dict.dict())
        else:
            q = urlencode(query_dict)
        if q:
            url = "%s?%s" % (url, q)

    method = (method_override or request.method).upper()
    data = None
    if method in ("POST", "PUT"):
        if request.POST:
            data = request.POST.dict()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            data = request.body
            ct = request.META.get("CONTENT_TYPE", "")
            if ct:
                headers["Content-Type"] = ct

    try:
        if method == "GET":
            resp = requests.get(url=url, headers=headers, timeout=TIMEOUT)
        elif method == "POST":
            resp = requests.post(url=url, headers=headers, data=data, timeout=TIMEOUT)
        elif method == "PUT":
            resp = requests.put(url=url, headers=headers, data=data, timeout=TIMEOUT)
        else:
            resp = requests.request(method=method, url=url, headers=headers, data=data, timeout=TIMEOUT)
    except Exception as e:
        return None, str(e)
    return resp, None


def proxy_node(request, node_code, path):
    """GET/POST proxy/node/<node_code>/<path> —— 通用节点页面/AJAX 代理"""
    # 登录校验（云端会话）
    if not f_sessionReadUserId(request):
        return _HttpResponse("未登录或会话已过期，请重新登录云端平台", status=401)

    node = NodeModel.objects.filter(code=node_code).first()
    if not node:
        return _HttpResponse("节点不存在", status=404)
    if node.state != 1:
        return _HttpResponse("节点离线或不可用（state=%s）" % node.state, status=503)

    # 路径白名单
    allowed = False
    for prefix in NODE_PROXY_PATH_PREFIXES:
        if path.startswith(prefix):
            allowed = True
            break
    if not allowed:
        return _HttpResponse("路径不在代理白名单内: %s" % path, status=403)

    # embed=1 由云端注入，避免边缘渲染整页框架
    # （controls 为布控表单提交成功后的回跳目标，control/index 为其等价路由；
    #   control/add、control/edit 为布控列表 iframe 内的添加/编辑跳转页）
    forward_get = request.GET.copy()
    if "embed" not in forward_get and path in (
            "stream/index", "controls", "control/index", "control/add", "control/edit"):
        forward_get["embed"] = "1"

    resp, err = _proxyForward(request, node, path, get_params=forward_get)
    if err:
        return _HttpResponse("节点请求失败: %s" % err, status=502)

    content_type = resp.headers.get("Content-Type", "")
    status = resp.status_code

    # HTML：重写绝对路径
    if "text/html" in content_type:
        html_text = resp.content.decode("utf-8", errors="replace")
        html_text = _proxyHtmlRewrite(html_text, node_code)
        return _HttpResponse(html_text, status=status, content_type=content_type)

    # JSON：重写下载链接等（兼容绝对 /xxx 与相对 static/xxx 两种形态；
    # 边缘页面 JS 会给相对路径补 '/' 前缀，若不重写会错误指向云端 static）
    if "application/json" in content_type:
        try:
            res_json = resp.json()
        except Exception:
            return _HttpResponse(resp.content, status=status, content_type=content_type)
        changed = False
        data_obj = res_json.get("data")
        if isinstance(data_obj, dict):
            for key in NODE_PROXY_JSON_REWRITE_KEYS:
                val = data_obj.get(key)
                if val and isinstance(val, str) and not val.startswith(("http://", "https://", "/proxy/")):
                    data_obj[key] = "/proxy/node/%s/%s" % (node_code, val.lstrip('/'))
                    changed = True
        # 布控表单预览等播放地址重写为云端 ZLM（经 inner hook 回源边缘）
        if _proxyRewriteStreamUrl(res_json, node_code, path):
            changed = True
        if changed:
            return _HttpResponse(json.dumps(res_json, ensure_ascii=False), status=status,
                                 content_type="application/json")
        return _HttpResponse(resp.content, status=status, content_type=content_type)

    # 其他（静态资源/文件流）：原样透传
    django_resp = _HttpResponse(resp.content, status=status, content_type=content_type)
    for h in ("Content-Disposition", "Content-Length", "Accept-Ranges", "Cache-Control"):
        if resp.headers.get(h):
            django_resp[h] = resp.headers.get(h)
    return django_resp