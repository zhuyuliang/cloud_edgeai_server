import os
import re
import shutil
import time
import platform
import requests
from datetime import datetime, timedelta
import json
import base64
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
import random
from django.http import HttpResponse
from framework.settings import BASE_DIR, PROJECT_UA,PROJECT_BUILT,PROJECT_VERSION, PROJECT_FLAG,PROJECT_ADMIN_START_TIMESTAMP,TIMEOUT,PROJECT_SUPPORT_MIN_VERSION
from app.utils.ZLMediaKit import ZLMediaKit
from app.utils.Settings import Settings
from app.utils.Config import Config
from app.utils.Logger import CreateLogger
from app.utils.OSSystem import OSSystem
from app.utils.Database import Database
from app.models import *
from django.utils.translation import gettext as _
# BASE_DIR # eai_admin目录的位置

g_filepath_config_json = os.path.join(BASE_DIR, "config.json")
g_filepath_settings_json = os.path.join(BASE_DIR, "settings.json")

g_config = Config(filepath=g_filepath_config_json)
g_settings = Settings(filepath=g_filepath_settings_json)

__log_dir = os.path.join(BASE_DIR, "log")
if not os.path.exists(__log_dir):
    os.makedirs(__log_dir)
g_logger = CreateLogger(filepath=os.path.join(__log_dir, "eai_admin%s.log" % (datetime.now().strftime("%Y%m%d-%H%M%S"))),
                        is_show_console=False,
                        log_debug=g_config.logDebug)

g_logger.info("%s v%s,%s" % (PROJECT_UA,PROJECT_VERSION, PROJECT_FLAG))
g_logger.info(PROJECT_BUILT)
g_logger.info("g_filepath_config_json=%s" % g_filepath_config_json)
g_logger.info("g_filepath_settings_json=%s" % g_filepath_settings_json)
g_logger.info("config.json:%s" % g_config.getStr())
g_logger.info("settings.json:%s" % g_settings.getStr())
g_logger.info("logDebug=%d" % g_config.logDebug)
g_osSystem = OSSystem()
g_machineMacs = g_osSystem.getAllMachineMacs()
g_machineMac = g_osSystem.getMachineMac(g_machineMacs)
g_logger.info("machineMacs=%s" % str(g_machineMacs))
g_logger.info("machineMac=%s" % str(g_machineMac))
g_zlm = ZLMediaKit(logger=g_logger, config=g_config)
g_database = Database(logger=g_logger)

PROJECT_SUPPORT_MIN_VERSION = PROJECT_SUPPORT_MIN_VERSION

def parseVersionToFloat(version):
    """将版本号（字符串或数值）安全解析为浮点数，解析失败返回 0，绝不抛异常。
    如 '2.3.5' -> 2.35, '2.7' -> 2.7, 'v2.3.5-beta' -> 2.35
    """
    if version is None:
        return 0
    s = str(version).strip()
    if not s:
        return 0
    m = re.search(r'(\d+(?:\.\d+)*)', s)
    if not m:
        return 0
    parts = m.group(1).split('.')
    value = 0.0
    for i, p in enumerate(parts):
        try:
            value += int(p) * (10.0 ** -i)
        except (ValueError, TypeError):
            return 0
    return value

g_session_key_user = "user"
g_session_key_captcha = "captcha"

class Services():

    def checkVersion(self, request_ip, request_port):
        __online = False
        __state = False
        __msg = _("未知错误")
        __info = {

        }
        headers = {
            "User-Agent": PROJECT_UA,
            "Content-Type": "application/json;"
        }
        __services_host = "https://www.yunzhieai.com"
        try:
            url = "%s/api/cloud_eai_admin/checkVersion" % __services_host
            osSystem = OSSystem()
            machine_cpu = osSystem.getMachineCpu()
            machine_gpu = "rknpu=%s,ascend=%s,nvidia=%s" % (osSystem.getMachineRknpu(), osSystem.getMachineAscend(), osSystem.getMachineNvidia())
            machineMacs = osSystem.getAllMachineMacs()
            machineMac = osSystem.getMachineMac(machineMacs)
            auth_info = {
                "machineMacs": machineMacs,
                "machineMac": machineMac
            }
            run_info = {}
            run_info["request_ip"] = request_ip
            run_info["request_port"] = request_port
            run_info["services_host"] = __services_host

            data = {
                "enable_update": 1 if g_settings.enable_update else 0,
                "flag": PROJECT_FLAG,
                "version": PROJECT_VERSION,
                "machine_mac": machineMac,
                "machine_cpu": machine_cpu,
                "machine_gpu": machine_gpu,
                "machine_version": str(platform.version()),
                "machine_machine": str(platform.machine()),
                "machine_release": str(platform.release()),
                "machine_node": str(platform.node()),
                "machine_architecture": str(platform.architecture()),
                "machine_uname": str(platform.uname()),
                "machine_win32_ver": "",
                "machine_system": str(osSystem.getSystemName()),
                "app_start_timestamp": PROJECT_ADMIN_START_TIMESTAMP,
                "current_timestamp": int(time.time()),
                "auth_info": str(auth_info),
                "run_info": str(run_info)
            }

            data_json = json.dumps(data)
            # res = requests.post(url=url, headers=headers, data=data_json, timeout=30)
            # demo
            res = HttpResponse(json.dumps({
                "code": 1000,
                "msg": "success",
                "data": {
                    "version": "2.3.7",
                    "pubdate": "2026-02-06",
                    "updateContent": "更新内容",
                }
            }), content_type="application/json")

            if res.status_code == 200:
                res_result = res.json()
                __msg = res_result["msg"]
                if res_result["code"] == 1000:
                    __info = res_result["data"]
                    __state = True
            else:
                __msg = "status_code=%d " % res.status_code

            __online = True
        except Exception as e:
            __online = False
            __msg = str(e)
            g_logger.error("checkVersion() e:%s" % str(e))

        return __online, __state, __msg, __info

g_services = Services()

class G_assistant():
    @staticmethod
    def __handleInstallByType(install,handle_type):
        __ret = False
        __msg = _("未知错误")

        try:
            osSystem = OSSystem()
            systemName = osSystem.getSystemName()
            g_logger.info("current system is %s" % systemName)

            if systemName == "Windows":
                # Windows重启软件
                if not os.path.exists(os.path.join(install, "eai.exe")):
                    raise Exception(_("软件安装路径配置不正确"))
                if not os.path.exists(os.path.join(install, "start.bat")):
                    raise Exception(_("软件安装路径配置不正确"))
                if not os.path.exists(os.path.join(install, "stop.bat")):
                    raise Exception(_("软件安装路径配置不正确"))
                if handle_type == 0:
                    # 安装路径正常
                    pass
                elif handle_type == 1:
                    # 启动App
                    os.popen("cd %s && start.bat" % install)
                elif handle_type == 2:
                    # 停止App
                    os.popen("cd %s && stop.bat" % install)
                else:
                    g_logger.error("undefined type:%d"%handle_type)

                __ret = True
                __msg = "success"

            elif systemName == "Linux" or systemName == "Darwin":
                # Linux重启软件
                if not os.path.exists(os.path.join(install, "eai")):
                    raise Exception(_("软件安装路径配置不正确"))
                if not os.path.exists(os.path.join(install, "start.sh")):
                    raise Exception(_("软件安装路径配置不正确"))
                if not os.path.exists(os.path.join(install, "stop.sh")):
                    raise Exception(_("软件安装路径配置不正确"))
                if handle_type == 0:
                    # 安装路径正常
                    pass
                elif handle_type == 1:
                    # 启动App
                    os.popen("cd %s && sh start.sh" % install)
                elif handle_type == 2:
                    # 停止App
                    os.popen("cd %s && sh stop.sh" % install)
                else:
                    g_logger.error("undefined type:%d"%handle_type)

                __ret = True
                __msg = "success"
            else:
                raise Exception("the current system is not supported!")

        except Exception as e:
            __msg = str(e)

        return __ret, __msg
    @staticmethod
    def checkInstall(install):
        __ret = False
        __msg = _("未知错误")
        g_logger.info("checkInstall() start install:%s" % install)
        __ret, __msg = G_assistant.__handleInstallByType(install, 0)
        g_logger.info("checkInstall() end ret=%d,msg=%s" % (__ret, __msg))
        return __ret, __msg

    @staticmethod
    def restartApp(install):
        __ret = False
        __msg = _("未知错误")
        g_logger.info("restartApp() start install:%s" % install)
        __ret,__msg = G_assistant.__handleInstallByType(install,1)
        g_logger.info("restartApp() end ret=%d,msg=%s" % (__ret, __msg))
        return __ret, __msg

    @staticmethod
    def stopApp(install):
        __ret = False
        __msg = _("未知错误")
        g_logger.info("stopApp() start install:%s" % install)
        __ret,__msg = G_assistant.__handleInstallByType(install,2)
        g_logger.info("stopApp() end ret=%d,msg=%s" % (__ret, __msg))
        return __ret, __msg

    @staticmethod
    def restartOS():
        __ret = False
        __msg = _("未知错误")
        g_logger.info("restartOS() start")
        try:
            osSystem = OSSystem()
            if osSystem.getSystemName() == "Windows":
                os.popen("shutdown /r /t 0")
            else:
                os.popen("reboot")
            __ret = True
            __msg = "success"
        except Exception as e:
            __msg = str(e)

        g_logger.info("restartOS() end ret=%d,msg=%s" % (__ret, __msg))
        return __ret, __msg

def f_parseGetParams(request):
    params = {}
    try:
        for k in request.GET:
            params.__setitem__(k, request.GET.get(k))
    except Exception as e:
        params = {}

    return params

def f_parsePostParams(request):
    params = {}
    for k in request.POST:
        params.__setitem__(k, request.POST.get(k))

    # 接收json方式上传的参数
    if not params:
        try:
            params = request.body.decode('utf-8')
            params = json.loads(params)
        except:
            params = {}

    return params
def f_parseRequestIp(request):
    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR') # 备用方案
    except Exception as e:
        g_logger.error("f_parseRequestIp() error: %s"%str(e))
        ip = "0.0.0.0"
    return ip

def f_parseRequestPort(request):
    return 0
def f_sessionReadUser(request):
    user = request.session.get(g_session_key_user)
    return user

def f_sessionReadUserId(request):
    try:
        user_id = f_sessionReadUser(request).get("id")
    except:
        user_id = 0
    return user_id

def f_checkRequestSafe(request):
    ret = False
    msg = _("未知错误")
    # 检查请求是否安全
    user_id = f_sessionReadUserId(request)
    if user_id:
        ret = True
        msg = "success"
    else:
        headers = request.headers
        Safe = headers.get("Safe")
        if Safe and Safe == g_config.eaiSafe:
            ret = True
            msg = "success"
        else:
            msg = "safe verify error"
    return ret,msg

def f_sessionLogout(request):
    if request.session.has_key(g_session_key_user):
        del request.session[g_session_key_user]
    if request.session.has_key(g_session_key_captcha):
        del request.session[g_session_key_captcha]

def f_responseJson(res):
    def json_dumps_default(obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        else:
            raise TypeError

    return HttpResponse(json.dumps(res, default=json_dumps_default), content_type="application/json")

def f_settingsReadData():
    return g_settings.data

def f_readSampleCountAndAnnotationCount(task_code):
    sample_count = g_database.select("select count(id) as count from eai_labeltk_sample where task_code='%s'" % task_code)
    sample_count = int(sample_count[0]["count"])
    sample_annotation_count = g_database.select(
        "select count(id) as count from eai_labeltk_sample where task_code='%s' and annotation_state=1" % task_code)
    sample_annotation_count = int(sample_annotation_count[0]["count"])

    return sample_count, sample_annotation_count

def f_checkNode(node_code):
    ret = False
    msg = _("未知错误")

    node = NodeModel.objects.filter(code=node_code)
    if len(node) > 0:
        node = node[0]
        if node.state == 0:
            msg = _("节点未同步")
        elif node.state == 1:
            ret = True
            msg = "success"
        elif node.state == 2:
            msg = _("节点离线")
        else:
            msg = _("节点版本低于%.3f") % parseVersionToFloat(PROJECT_SUPPORT_MIN_VERSION)
    else:
        msg = _("节点不存在")

    return ret, msg, node

class EaiApi():

    def openDiscover(self,node):
        is_online = False
        ret = False
        msg = _("未知错误")
        info = {}
        try:
            headers = {
                "User-Agent": PROJECT_UA,
                "Content-Type": "application/json;",
                "Eai-Secret": node.eai_safe
            }
            res = requests.get(url='%s' % node.address,headers=headers, timeout=TIMEOUT)
            is_online = True # 表示节点在线
            try:
                res = requests.get(url='%s/open/discover?is_auth=1' % node.address,
                                   headers=headers, timeout=TIMEOUT)
                if res.status_code == 200:
                    res_result = res.json()
                    g_logger.info("openDiscover() node.address=%s, status=%d, resp=%s" % (
                        node.address, res.status_code, json.dumps(res_result, ensure_ascii=False)))
                    msg = res_result.get("msg")
                    if int(res_result.get("code", 0)) == 1000:
                        info = res_result.get("info") or {}
                        if isinstance(info, dict):
                            g_logger.info("openDiscover() node.address=%s, project_version=%s, project_flag=%s, node_code=%s, node_name=%s" % (
                                node.address,
                                info.get("project_version"),
                                info.get("project_flag"),
                                info.get("code"),
                                info.get("name")))
                        ret = True
                else:
                    raise Exception("status=%d" % res.status_code)
            except Exception as e:
                raise e
        except Exception as e:
            msg = str(e)
        print(is_online,ret,msg,info)
        return is_online,ret, msg, info

    # 获取节点所有视频数据
    def getAllStreamData(self,node):
        ret = False
        msg = _("未知错误")
        data = []
        try:
            headers = {
                "User-Agent": PROJECT_UA,
                "Content-Type": "application/json;",
                "Eai-Secret": node.eai_safe
            }
            res = requests.get(url='%s/open/getAllStreamData' % node.address,
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

        return ret, msg, data

    def getAllAlgroithmFlowData(self,node):
        ret = False
        msg = _("未知错误")
        data = []
        try:
            headers = {
                "User-Agent": PROJECT_UA,
                "Content-Type": "application/json;",
                "Eai-Secret": node.eai_safe
            }
            res = requests.get(url='%s/open/getAllAlgroithmFlowData' % node.address,
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

        return ret, msg, data

# 读取节点媒体源数据（eai_node_media_source，由 f_syncNodeMediaSource 同步自边缘）
# 返回字典字段: code, app, name, nickname, forward_state, online_state
def f_dbReadStreamData():
    data = []
    for obj in NodeMediaSourceModel.objects.all().order_by("id"):
        data.append({
            "code": obj.source_code,
            "app": obj.app,
            "name": obj.name,
            "nickname": obj.nickname if obj.nickname else obj.name,
            "forward_state": obj.forward_state,
            "online_state": obj.online_state,
        })
    return data

# 读取算法流数据（eai_node_algorithm_flow）
# 返回字典字段: code, name
def f_dbReadAlgorithmFlowData():
    data = []
    for obj in NodeAlgorithmFlowModel.objects.filter(state=1).order_by("sort", "id"):
        data.append({
            "code": obj.flow_code,
            "name": obj.flow_name,
        })
    return data

# zlm 分组名(app)转中文显示名
def f_replaceGroupName(group_name):
    GROUP_NAME_MAP = {
        "live": "直播流",
        "rtp": "GB28181",
        "analyzer": "算法流",
    }
    return GROUP_NAME_MAP.get(group_name, group_name)

# 同步节点媒体源数据（av_media_source → eai_node_media_source）
# 边缘返回字段: code, nickname, source_type, app, name, forward_state, state
def f_syncNodeMediaSource(node, stream_data):
    g_logger.info("f_syncNodeMediaSource() node_code=%s, count=%d" % (node.code, len(stream_data)))

    MEDIA_SOURCE_TYPE = {1, 2, 3, 4, 5}
    now = datetime.now()
    seen_codes = set()

    for d in stream_data:
        source_code = str(d.get("code", "")).strip()
        if not source_code:
            continue
        seen_codes.add(source_code)

        try:
            source_type = int(d.get("source_type", 1) or 1)
        except (TypeError, ValueError):
            source_type = 1
        if source_type not in MEDIA_SOURCE_TYPE:
            source_type = 1

        obj = NodeMediaSourceModel.objects.filter(
            node_code=node.code, source_code=source_code).first()
        if not obj:
            obj = NodeMediaSourceModel()
            obj.node_code = node.code
            obj.source_code = source_code
            obj.create_time = now  # auto_now_add 首次保存后不再变化

        try:
            forward_state = int(d.get("forward_state", 0) or 0)
        except (TypeError, ValueError):
            forward_state = 0
        try:
            online_state = int(d.get("state", 0) or 0)
        except (TypeError, ValueError):
            online_state = 0

        obj.source_type = source_type
        obj.app = str(d.get("app", "") or "")[:50]
        obj.name = str(d.get("name", "") or "")[:50]
        obj.nickname = str(d.get("nickname", "") or "")[:200]
        obj.forward_state = 1 if forward_state == 1 else 0
        obj.online_state = online_state
        obj.extra = json.dumps(d, ensure_ascii=False, default=str)
        obj.last_update_time = now
        obj.save()

    # 删除边缘已不存在的媒体源
    deleted_count, _ = NodeMediaSourceModel.objects.filter(
        node_code=node.code).exclude(source_code__in=seen_codes).delete()
    if deleted_count:
        g_logger.info("f_syncNodeMediaSource() node_code=%s 删除失效媒体源%d条" % (node.code, deleted_count))


# 同步节点信息
def f_syncNode(code=None):
    g_logger.info("f_syncNode() code=%s"%str(code))

    eai_api = EaiApi()

    success_count = 0
    error_count = 0
    if code:
        # 指定节点
        nodes = []
        node = NodeModel.objects.filter(code=code).first()
        nodes.append(node)
    else:
        # 所有节点
        nodes = NodeModel.objects.all()

    for node in nodes:
        __is_online = False
        __ret = False
        __msg = _("未知错误")

        try:
            __is_online, __ret, __msg, __info = eai_api.openDiscover(node)
            if __is_online:
                if __ret:
                    __raw_version = __info.get("project_version", 0)
                    project_version = parseVersionToFloat(__raw_version)
                    g_logger.info("f_syncNode() node.code=%s, 节点返回 project_version 原始值=%s, 解析为=%s, project_flag=%s" % (
                        node.code, __raw_version, project_version, __info.get("project_flag")))

                    node.version = project_version
                    node.flag = __info.get("project_flag")
                    node.system_name = __info.get("system_name")
                    node.machine_node = __info.get("machine_node")

                    node_code = __info.get("code","").strip()
                    if node_code:
                        node.node_code = node_code
                    else:
                        node.node_code = __info.get("name","").strip()

                    node.node_host = __info.get("host","").strip()

                    # TODO 授权信息start
                    __info_auth = __info.get("auth")
                    if __info_auth:
                        __info_auth_info = __info_auth.get("info")
                        if __info_auth_info:
                            node.machine_mac = __info_auth_info.get("machineMac")
                            node.is_auth = int(__info_auth_info.get("isAuth", 0))
                            node.is_multi_process = int(__info_auth_info.get("isMultiProcess", 0))
                            node.max_count = int(__info_auth_info.get("maxCount", 0))
                            node.desc = __info_auth_info.get("desc")
                    node.auth_info = json.dumps(__info_auth)
                    # 授权信息end

                    isSyncNodeData = True

                    if isSyncNodeData:
                        g_logger.info("f_syncNode() 开始同步节点视频数据 node_code=%s"%node.code)
                        __ret,__msg,__stream_data = eai_api.getAllStreamData(node)
                        now = datetime.now()
                        for d in __stream_data:
                            stream_code = d.get("code")
                            stream_nickname = d.get("nickname")
                            nodeStream = NodeStreamModel.objects.filter(stream_code=stream_code).first()
                            if nodeStream:
                                nodeStream.stream_nickname = stream_nickname
                                node_codes = nodeStream.node_codes
                                node_codes_list = node_codes.split(",")
                                node_codes_set = set(node_codes_list)
                                node_codes_set.add(node.code)
                                node_codes_list = list(node_codes_set)
                                nodeStream.node_codes = ",".join(node_codes_list)
                            else:
                                nodeStream = NodeStreamModel()
                                nodeStream.sort = 0
                                nodeStream.stream_code = stream_code
                                nodeStream.stream_nickname = stream_nickname
                                nodeStream.node_codes = node.code
                                nodeStream.state = 0
                                nodeStream.create_time = now
                            nodeStream.last_update_time = now
                            nodeStream.save()

                        g_logger.info("f_syncNode() 开始同步节点媒体源数据 node_code=%s" % node.code)
                        # 边缘新版(open/getAllStreamData)返回 av_media_source 全量字段，可直接同步
                        try:
                            f_syncNodeMediaSource(node, __stream_data)
                        except Exception as e:
                            g_logger.error("f_syncNode() 同步媒体源失败 node_code=%s, msg=%s" % (node.code, str(e)))

                        g_logger.info("f_syncNode() 开始同步节点算法数据 node_code=%s" % node.code)
                        __ret,__msg,__flow_data = eai_api.getAllAlgroithmFlowData(node)
                        for d in __flow_data:
                            flow_code = d.get("code")
                            flow_name = d.get("name")
                            nodeFlow = NodeAlgorithmFlowModel.objects.filter(flow_code=flow_code).first()
                            if nodeFlow:
                                nodeFlow.flow_name = flow_name

                                node_codes = nodeFlow.node_codes
                                node_codes_list = node_codes.split(",")
                                node_codes_set = set(node_codes_list)
                                node_codes_set.add(node.code)
                                node_codes_list = list(node_codes_set)
                                nodeFlow.node_codes = ",".join(node_codes_list)
                            else:
                                nodeFlow = NodeAlgorithmFlowModel()
                                nodeFlow.sort = 0
                                nodeFlow.flow_code = flow_code
                                nodeFlow.flow_name = flow_name
                                nodeFlow.node_codes = node.code
                                nodeFlow.state = 0
                                nodeFlow.create_time = now
                            nodeFlow.last_update_time = now
                            nodeFlow.save()

                    node.state = 1
                    # if project_version > 4:
                    #     if project_version < PROJECT_SUPPORT_XCMS_MIN_VERSION:
                    #         node.state = 3
                    #         raise Exception("v4版本不能低于%.3f" % PROJECT_SUPPORT_XCMS_MIN_VERSION)

                    # elif project_version > 3:
                    #     if project_version < PROJECT_SUPPORT_V3_MIN_VERSION:
                    #         node.state = 3
                    #         raise Exception("v3版本不能低于%.3f" % PROJECT_SUPPORT_V3_MIN_VERSION)
                    # if project_version > 4:
                        # if project_version < PROJECT_SUPPORT_XCMS_MIN_VERSION:
                        #     node.state = 3
                        #     raise Exception("v4版本不能低于%.3f" % PROJECT_SUPPORT_XCMS_MIN_VERSION)

                    # else:
                    #     raise Exception("节点版本不支持")

                else:
                    # node.state = 4
                    # raise Exception("读取节点信息失败")
                    node.state = 3
                    g_logger.info("f_syncNode() node.code=%s, openDiscover 失败 is_online=%s, ret=%s, msg=%s, info=%s" % (
                        node.code, __is_online, __ret, __msg, json.dumps(__info, ensure_ascii=False, default=str)))
                    raise Exception("节点版本不支持")
            else:
                node.state = 2
                raise Exception("节点离线")
        except Exception as e:
            __msg = str(e)
            print("f_syncNode() node.code=%s,msg=%s" % (node.code, __msg))
            g_logger.error("f_syncNode() node.code=%s,msg=%s" % (node.code, __msg))

        if __ret:
            success_count += 1
        else:
            error_count += 1
        node.last_update_time = datetime.now()
        node.save()



    ret = True
    msg = _("成功%d条，失败%d条") % (success_count, error_count)
    print("f_syncNode() ret=%d,msg=%s"%(ret,msg))
    g_logger.info("f_syncNode() ret=%d,msg=%s"%(ret,msg))

    return ret, msg

