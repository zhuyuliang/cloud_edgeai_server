from app.views.ViewsBase import *
from django.shortcuts import render
from framework.settings import PROJECT_VERSION, PROJECT_FLAG
from django.utils.translation import gettext as _
def index(request):
    context = {
        "settings": f_settingsReadData(),
        "project_version": PROJECT_VERSION,
        "project_flag": PROJECT_FLAG,
    }
    return render(request, 'app/version/index.html', context)

# 检查服务端最新版本
def api_getCheckVersion(request):
    ret = False
    msg = _("未知错误")
    info = {
        "historyVersionUrl": g_settings.check_version_download_url
    }
    request_ip = f_parseRequestIp(request)
    request_port = f_parseRequestPort(request)
    __online, __state, __msg, __info = g_services.checkVersion(request_ip, request_port)
    if __online:
        if __state:
            # 发现新版本
            info["version"] = __info.get("version")
            info["pubdate"] = __info.get("pubdate")
            info["updateContent"] = __info.get("updateContent","").split("\\n")
            info["historyVersionUrl"] = __info.get("historyVersionUrl","")
            info["url"] = __info.get("url","")

            ret = True
            msg = "success"
        else:
            msg = _("未发现新版本")
    else:
        msg = _("无法联网检测新版本")

    res = {
        "code": 1000 if ret else 0,
        "msg": msg,
        "info": info
    }
    return f_responseJson(res)
