import time
from app.views.ViewsBase import *
from app.models import *
from django.shortcuts import render, redirect
from app.utils.Utils import gen_random_code_s
from django.utils.translation import gettext as _


def _node_code_from_referer(request):
    """从 Referer 的 /proxy/node/<code>/ 前缀提取节点编号。

    用于修复：iframe 代理页内 JS 跳转泄漏到云端路由（未带 node_code）时，
    依据 Referer 中的代理前缀直接重定向回代理路径，
    避免云端整壳页面（含侧边栏/内层 iframe）在 iframe 内嵌套叠加。
    """
    referer = request.META.get("HTTP_REFERER", "")
    marker = "/proxy/node/"
    pos = referer.find(marker)
    if pos < 0:
        return ""
    code = referer[pos + len(marker):].split("/", 1)[0]
    return code.strip()


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

    # 新版：iframe 双跳嵌入边缘统一布控管理页（proxy/node/<code>/controls?embed=1）
    return render(request, 'app/control/index_v2.html', context)

def add(request):
    """新增布控页 —— iframe 双跳：页面壳由云端渲染，表单直连边缘（经代理）。

    P2 改造：不再拉取边缘 JSON context 渲染云端表单（老链路依赖边缘
    openAddContext 返回 JSON，与边缘新版页面能力脱节），改为复用
    StreamView.proxy_node 代理边缘 web_add_control 页面（embed=1 隐藏框架），
    保持与边缘本地完全一致的新增体验。
    """
    if request.method != 'GET':
        return render(request, 'app/message.html',
                      {"msg": "request method not supported", "is_success": False,
                       "redirect_url": "/control/index"})

    params = f_parseGetParams(request)
    node_code = str(params.get('node_code', "")).strip()
    if node_code == "":
        # iframe 代理页内跳转泄漏到云端路由时（未带 node_code），
        # 依据 Referer 重定向回代理路径（单层 iframe），避免整壳页面嵌套叠加
        node_code = _node_code_from_referer(request)
        if node_code:
            suffix = ""
            if params.get("camera_code"):
                suffix = "?camera_code=%s" % params.get("camera_code")
            return redirect("/proxy/node/%s/control/add%s" % (node_code, suffix))
        return redirect("/control/index")

    __node_ret, __node_msg, node = f_checkNode(node_code=node_code)
    if not __node_ret:
        return render(request, 'app/message.html',
                      {"msg": __node_msg, "is_success": False, "redirect_url": "/control/index"})

    context = {
        "node_code": node_code,
        "node_nickname": node.nickname,
        "page_title": _("新增布控"),
        "iframe_src": "/proxy/node/%s/control/add?embed=1" % node_code,
        "redirect_url": "/control/index?node_code=%s" % node_code,
    }
    if params.get("camera_code"):
        context["iframe_src"] += "&camera_code=%s" % params.get("camera_code")
    return render(request, 'app/control/iframe.html', context)

def api_openAdd(request):
    ret = False
    msg = _("未知错误")
    if request.method == 'POST':
        __check_ret, __check_msg = f_checkRequestSafe(request)
        if __check_ret:
            params = f_parsePostParams(request)
            g_logger.info("ControlView.openAdd() params:%s" % str(params))
            node_code = str(params.get('node_code', "")).strip()

            __node_ret, __node_msg, node = f_checkNode(node_code=node_code)
            if __node_ret:
                try:
                    headers = {
                        "User-Agent": PROJECT_UA,
                        "Content-Type": "application/json;",
                        "Eai-Secret": node.eai_safe
                    }
                    res = requests.post(url='%s/control/openAdd' % node.address,
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
    g_logger.info("ControlView.openAdd() res:%s" % str(res))
    return f_responseJson(res)
def edit(request):
    """编辑布控页 —— iframe 双跳（同 add()，代理边缘 web_edit_control）。"""
    if request.method != 'GET':
        return render(request, 'app/message.html',
                      {"msg": "request method not supported", "is_success": False,
                       "redirect_url": "/control/index"})

    params = f_parseGetParams(request)
    code = str(params.get('code', "")).strip()
    node_code = str(params.get('node_code', "")).strip()
    if node_code == "" and code != "":
        # 同 add()：Referer 修复 iframe 内跳转泄漏，重定向回代理路径
        node_code = _node_code_from_referer(request)
        if node_code:
            return redirect("/proxy/node/%s/control/edit?code=%s" % (node_code, code))
    if node_code == "" or code == "":
        return redirect("/control/index")

    __node_ret, __node_msg, node = f_checkNode(node_code=node_code)
    if not __node_ret:
        return render(request, 'app/message.html',
                      {"msg": __node_msg, "is_success": False, "redirect_url": "/control/index"})

    context = {
        "node_code": node_code,
        "node_nickname": node.nickname,
        "page_title": _("编辑布控"),
        "iframe_src": "/proxy/node/%s/control/edit?embed=1&code=%s" % (node_code, code),
        "redirect_url": "/control/index?node_code=%s" % node_code,
    }
    return render(request, 'app/control/iframe.html', context)

def api_openEdit(request):
    ret = False
    msg = _("未知错误")
    if request.method == 'POST':
        __check_ret, __check_msg = f_checkRequestSafe(request)
        if __check_ret:
            params = f_parsePostParams(request)
            g_logger.info("ControlView.openEdit() params:%s" % str(params))
            node_code = str(params.get('node_code', "")).strip()

            __node_ret, __node_msg, node = f_checkNode(node_code=node_code)
            if __node_ret:
                try:
                    headers = {
                        "User-Agent": PROJECT_UA,
                        "Content-Type": "application/json;",
                        "Eai-Secret": node.eai_safe
                    }
                    res = requests.post(url='%s/control/openEdit' % node.address,
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
    g_logger.info("ControlView.openEdit() res:%s" % str(res))
    return f_responseJson(res)

def api_openDel(request):
    ret = False
    msg = _("未知错误")
    if request.method == 'POST':
        __check_ret, __check_msg = f_checkRequestSafe(request)
        if __check_ret:
            params = f_parsePostParams(request)
            g_logger.info("ControlView.openDel() params:%s" % str(params))
            node_code = str(params.get('node_code', "")).strip()

            __node_ret, __node_msg, node = f_checkNode(node_code=node_code)
            if __node_ret:
                try:
                    headers = {
                        "User-Agent": PROJECT_UA,
                        "Content-Type": "application/json;",
                        "Eai-Secret": node.eai_safe
                    }
                    res = requests.post(url='%s/control/openDel' % node.address,
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
    g_logger.info("ControlView.openDel() res:%s" % str(res))
    return f_responseJson(res)

def api_openCopy(request):
    ret = False
    msg = _("未知错误")
    if request.method == 'POST':
        __check_ret, __check_msg = f_checkRequestSafe(request)
        if __check_ret:
            params = f_parsePostParams(request)
            g_logger.info("ControlView.openCopy() params:%s" % str(params))
            node_code = str(params.get('node_code', "")).strip()

            __node_ret, __node_msg, node = f_checkNode(node_code=node_code)
            if __node_ret:
                try:
                    headers = {
                        "User-Agent": PROJECT_UA,
                        "Content-Type": "application/json;",
                        "Eai-Secret": node.eai_safe
                    }
                    res = requests.post(url='%s/control/openCopy' % node.address,
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
    g_logger.info("ControlView.openCopy() res:%s" % str(res))
    return f_responseJson(res)

def api_openSettings(request):
    # 快捷设置
    ret = False
    msg = _("未知错误")
    if request.method == 'POST':
        __check_ret, __check_msg = f_checkRequestSafe(request)
        if __check_ret:
            params = f_parsePostParams(request)
            g_logger.info("ControlView.openSettings() params:%s" % str(params))
            node_code = str(params.get('node_code', "")).strip()

            __node_ret, __node_msg, node = f_checkNode(node_code=node_code)
            if __node_ret:
                try:
                    headers = {
                        "User-Agent": PROJECT_UA,
                        "Content-Type": "application/json;",
                        "Eai-Secret": node.eai_safe
                    }
                    res = requests.post(url='%s/control/openSettings' % node.address,
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
    g_logger.info("ControlView.openSettings() res:%s" % str(res))
    return f_responseJson(res)

def api_openLog(request):
    ret = False
    msg = _("未知错误")
    data = []
    if request.method == 'GET':
        __check_ret, __check_msg = f_checkRequestSafe(request)
        if __check_ret:
            params = f_parseGetParams(request)
            g_logger.info("ControlView.openLog() params:%s" % str(params))

            controlCode = params.get("controlCode")
            node_code = str(params.get('node_code', "")).strip()

            __node_ret, __node_msg, node = f_checkNode(node_code=node_code)
            if __node_ret:
                try:
                    headers = {
                        "User-Agent": PROJECT_UA,
                        "Content-Type": "application/json;",
                        "Eai-Secret": node.eai_safe
                    }
                    res = requests.get(url='%s/control/openLog?controlCode=%s' % (node.address, controlCode),
                                       headers=headers, timeout=TIMEOUT)

                    if res.status_code == 200:
                        res_result = res.json()
                        msg = res_result.get("msg")
                        if int(res_result.get("code", 0)) == 1000:
                            data = res_result.get("data")
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
        "msg": msg,
        "data": data
    }
    g_logger.info("ControlView.openLog() res:%s" % str(res))
    return f_responseJson(res)

def api_openIndex(request):
    ret = False
    msg = _("未知错误")
    data = []
    pageData = {}

    if request.method == 'GET':
        __check_ret, __check_msg = f_checkRequestSafe(request)
        if __check_ret:
            params = f_parseGetParams(request)
            page = params.get('p', 1)
            page_size = params.get('ps', 10)
            search_text = str(params.get('search_text', "")).strip() # v4.638新增
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

                    res = requests.get(url='%s/control/openIndex?p=%s&ps=%s&search_text=%s' % (node.address, page, page_size, search_text),
                                       headers=headers, timeout=TIMEOUT)

                    if res.status_code == 200:
                        res_result = res.json()
                        msg = res_result.get("msg")
                        if int(res_result.get("code", 0)) == 1000:
                            data = res_result.get("data")
                            pageData = res_result.get("pageData")

                            # 本地 join 媒体源昵称（eai_node_media_source 为 P1 同步的
                            # 边缘媒体源快照，减少回源查询；缺省回退边缘返回的 stream_nickname）
                            try:
                                __ms_dict = {}
                                for __ms in NodeMediaSourceModel.objects.filter(node_code=node_code):
                                    __ms_dict["%s_%s" % (__ms.app, __ms.name)] = __ms.nickname
                                for __d in data or []:
                                    __nick = __ms_dict.get("%s_%s" % (__d.get("stream_app"), __d.get("stream_name")))
                                    if __nick:
                                        __d["stream_nickname"] = __nick
                            except Exception as __e:
                                g_logger.warning("ControlView.openIndex() join nickname error: %s" % str(__e))

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
        "msg": msg,
        "data": data,
        "pageData": pageData
    }
    return f_responseJson(res)
def api_openHandleAllControl(request):
    ret = False
    msg = _("未知错误")
    if request.method == 'POST':
        __check_ret, __check_msg = f_checkRequestSafe(request)
        if __check_ret:
            params = f_parsePostParams(request)
            g_logger.info("ControlView.openHandleAllControl() params:%s" % str(params))
            node_code = str(params.get('node_code', "")).strip()

            __node_ret, __node_msg, node = f_checkNode(node_code=node_code)
            if __node_ret:
                try:
                    headers = {
                        "User-Agent": PROJECT_UA,
                        "Content-Type": "application/json;",
                        "Eai-Secret": node.eai_safe
                    }

                    res = requests.post(url='%s/control/openHandleAllControl' % node.address,
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
    g_logger.info("ControlView.openHandleAllControl() res:%s" % str(res))
    return f_responseJson(res)
def api_openStartControl(request):
    # 开始执行布控
    ret = False
    msg = _("未知错误")

    if request.method == 'POST':
        __check_ret, __check_msg = f_checkRequestSafe(request)
        if __check_ret:
            params = f_parsePostParams(request)
            g_logger.info("ControlView.openStartControl() params:%s" % str(params))

            node_code = str(params.get('node_code', "")).strip()

            __node_ret, __node_msg, node = f_checkNode(node_code=node_code)
            if __node_ret:
                try:
                    headers = {
                        "User-Agent": PROJECT_UA,
                        "Content-Type": "application/json;",
                        "Eai-Secret": node.eai_safe
                    }

                    res = requests.post(url='%s/control/openStartControl' % node.address,
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
    g_logger.info("ControlView.openStartControl() res:%s" % str(res))
    return f_responseJson(res)
def api_openStopControl(request):
    # 停止执行布控
    ret = False
    msg = _("未知错误")

    if request.method == 'POST':
        __check_ret, __check_msg = f_checkRequestSafe(request)
        if __check_ret:
            params = f_parsePostParams(request)
            g_logger.info("ControlView.openStopControl() params:%s" % str(params))

            node_code = str(params.get('node_code', "")).strip()

            __node_ret, __node_msg, node = f_checkNode(node_code=node_code)
            if __node_ret:
                try:
                    headers = {
                        "User-Agent": PROJECT_UA,
                        "Content-Type": "application/json;",
                        "Eai-Secret": node.eai_safe
                    }
                    res = requests.post(url='%s/control/openStopControl' % node.address,
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
    g_logger.info("ControlView.openStopControl() res:%s" % str(res))
    return f_responseJson(res)
