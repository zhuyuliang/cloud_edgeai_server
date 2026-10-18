import os
import time
import json
import base64
import random
import hashlib
import hmac as hmac_lib
from datetime import datetime, timedelta
from app.views.ViewsBase import *
from app.models import *
from app.utils.TarUtils import TarUtils
from app.utils.AlarmUtils import AlarmUtils
from app.utils.Utils import gen_random_code_s
from django.utils.translation import gettext as _
from django.shortcuts import render, redirect
from app.utils.Utils import buildPageLabels
from app.utils.OSSystem import OSSystem

# ─────────────────── 边缘推送验签（算法与边缘 PushSigner 一致） ───────────────────
PUSH_HEADER_SIGNATURE = "X-Push-Signature"
PUSH_HEADER_TIMESTAMP = "X-Push-Timestamp"
PUSH_SIGN_TOLERANCE_SECONDS = 300  # 时间戳容差 ±5 分钟

def f_verifyPushSign(request, payload):
    """
    校验边缘推送签名。
    签名算法: HMAC-SHA256(secret, "<timestamp>.<紧凑排序JSON>")
    pushSecret 为空（云端与边缘均未配置）时跳过验证（与边缘 PushSigner.verify_sign 语义一致）。
    :return: (ok, msg)
    """
    secret = getattr(g_config, "pushSecret", "") or ""
    signature = request.META.get("HTTP_X_PUSH_SIGNATURE", "") or request.headers.get("X-Push-Signature", "")
    timestamp_str = str(request.META.get("HTTP_X_PUSH_TIMESTAMP", "") or request.headers.get("X-Push-Timestamp", ""))
    if not secret:
        return True, "push secret not configured, skip verify"
    if not signature:
        return False, "missing X-Push-Signature header"
    try:
        timestamp = int(timestamp_str)
    except Exception:
        return False, "invalid X-Push-Timestamp header"
    if abs(int(time.time()) - timestamp) > PUSH_SIGN_TOLERANCE_SECONDS:
        return False, "push timestamp expired"
    try:
        payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        sign_data = "%s.%s" % (timestamp, payload_str)
        expected = hmac_lib.new(secret.encode('utf-8'), sign_data.encode('utf-8'), hashlib.sha256).hexdigest()
        if hmac_lib.compare_digest(expected, signature):
            return True, "success"
        return False, "signature mismatch"
    except Exception as e:
        return False, "signature verify error: %s" % str(e)

def f_parsePushJsonBody(request):
    """
    解析推送 JSON body（与验签算法保持一致：边缘 requests.post(json=...) 默认 ensure_ascii）。
    :return: (payload_dict, raw_body)
    """
    try:
        raw_body = request.body.decode('utf-8')
        payload = json.loads(raw_body)
        if not isinstance(payload, dict):
            return None, raw_body
        return payload, raw_body
    except Exception:
        return None, ""

def f_getAlarmInfoByCode(alarm_code):

    alarm = NodeAlarmModel.objects.filter(code=alarm_code).first()
    if alarm:
        video_count = alarm.video_count
        video_is_wav = 0
        if video_count > 0:
            videoUrl = alarm.video_path
            # 兼容老数据：相对路径拼接 storage 前缀，push 数据已是完整可访问地址
            if videoUrl and not videoUrl.startswith(("http://", "https://", "/storage/")):
                videoUrl = g_config.storageDir_www + videoUrl
            if videoUrl.endswith("wav"):
                video_is_wav = 1
        else:
            videoUrl = ""

        image_count = alarm.image_count
        other_image_count = alarm.other_image_count

        if image_count > 0:
            imageUrl = alarm.image_path
            if imageUrl and not imageUrl.startswith(("http://", "https://", "/storage/")):
                imageUrl = g_config.storageDir_www + imageUrl
        else:
            imageUrl = "/static/images/720p.jpg"

        # 获取并拼接所有图片start
        imageUrlArray = []
        if image_count > 0:
            imageUrlArray.append(imageUrl)
            image_path = alarm.image_path

            if other_image_count > 0:
                image_path_ss = image_path.split(".")
                if len(image_path_ss) == 2:
                    image_path_l = image_path_ss[0]
                    image_path_r = image_path_ss[1]
                    for i in range(other_image_count):
                        __imageUrl = "%s_%d.%s" % (image_path_l, (i + 1), image_path_r)
                        if not __imageUrl.startswith(("http://", "https://", "/storage/")):
                            __imageUrl = g_config.storageDir_www + __imageUrl
                        imageUrlArray.append(__imageUrl)
        # 获取并拼接所有图片end

        node_nickname = alarm.node_code
        try:
            __node = NodeModel.objects.filter(code=alarm.node_code).first()
            if __node:
                node_nickname = __node.nickname
        except Exception as e:
            g_logger.warning("AlarmView.f_getAlarmInfoByCode() load node error:%s" % str(e))

        alarm_info = {
            "id": alarm.id,
            "code": alarm.code,
            "event_id": alarm.event_id,
            "node_code": alarm.node_code,
            "node_nickname": node_nickname,
            "control_code": alarm.control_code,
            "alarm_category": alarm.alarm_category,
            "stream_code": alarm.stream_code,
            "flow_code": alarm.flow_code,
            "flow_name": alarm.flow_name,
            "task_name": alarm.task_name,
            "flag": alarm.flag,
            "draw_type": alarm.draw_type,
            "video_count": video_count,
            "video_is_wav": video_is_wav,
            "videoUrl": videoUrl,
            "image_count": image_count,
            "imageUrl": imageUrl,
            "imageUrlArray": imageUrlArray,  # 所有图片的地址，包括：主封面+其余图
            "risk_level": alarm.level if alarm.level is not None else 0,
            "desc": alarm.desc,
            "deal_info": alarm.deal_info,
            "create_time": alarm.create_time,
            "create_time_str": alarm.create_time.strftime("%Y-%m-%d %H:%M:%S") if alarm.create_time else "",
            "state": alarm.state,
            "review_remark": alarm.review_remark
        }
        return alarm_info

    return None

# ─────────────────── P3: 告警页面（镜像边缘 alarms/* 分类） ───────────────────
# alarm_category: 0事件 1车牌 2人脸 3计数；state: 0未读 1未处理 2已处理 3误报

ALARM_CATEGORY_NAMES = {0: _("事件告警"), 1: _("车牌告警"), 2: _("人脸告警"), 3: _("计数告警")}
ALARM_STATE_NAMES = {0: _("未读"), 1: _("未处理"), 2: _("已处理"), 3: _("误报")}
ALARM_RISK_NAMES = {0: _("低风险"), 1: _("中风险"), 2: _("高风险")}

def _alarmListContext(request, alarm_category, page_title):
    """告警分类列表页共用 context（event/carplate/face/history 复用）。"""
    context = {
        "settings": f_settingsReadData(),
        "page_title": page_title,
        "alarm_category": alarm_category,
    }
    context["nodes"] = NodeModel.objects.all().order_by("sort").values("code", "nickname")
    context["states"] = [{"value": k, "name": v} for k, v in ALARM_STATE_NAMES.items()]

    now_date = datetime.now()
    context["startDate"] = (now_date - timedelta(days=6)).strftime("%Y-%m-%d")
    context["endDate"] = now_date.strftime("%Y-%m-%d")
    return context

def page_event(request):
    return render(request, 'app/alarm/list.html', _alarmListContext(request, 0, "事件告警"))

def page_carplate(request):
    return render(request, 'app/alarm/list.html', _alarmListContext(request, 1, "车牌告警"))

def page_face(request):
    return render(request, 'app/alarm/list.html', _alarmListContext(request, 2, "人脸告警"))

def page_count(request):
    """计数告警页：数据来自 eai_node_statistic_alarm。"""
    context = {
        "settings": f_settingsReadData(),
        "page_title": _("计数告警"),
        "nodes": NodeModel.objects.all().order_by("sort").values("code", "nickname"),
    }
    return render(request, 'app/alarm/count.html', context)

def _statisticHistoryQuery(request):
    """
    计数历史查询：归档周期 + 当前进行中周期（来自实时表）。
    :return: (ret, msg, rows) rows 按 period_end 倒序（进行中在最前）
    """
    params = f_parseGetParams(request)
    node_code = str(params.get("node_code", "")).strip()
    control_code = str(params.get("control_code", "")).strip()
    task_name = str(params.get("task_name", "")).strip()
    if not node_code or not control_code:
        return False, _("缺少节点或布控参数"), []

    qs = NodeStatisticHistoryModel.objects.filter(
        node_code=node_code, control_code=control_code)
    if task_name:
        qs = qs.filter(task_name=task_name)
    rows = []
    now = datetime.now()
    for h in qs.order_by("-period_end"):
        rows.append({
            "id": h.id,
            "node_code": h.node_code,
            "control_code": h.control_code,
            "task_name": h.task_name,
            "enter_num": h.enter_num,
            "leave_num": h.leave_num,
            "total_num": h.total_num,
            "snap_url": h.snap_url or "",
            "reset_strategy": h.reset_strategy or "manual",
            "period_start": h.period_start.strftime("%Y-%m-%d %H:%M:%S") if h.period_start else "",
            "period_end": h.period_end.strftime("%Y-%m-%d %H:%M:%S") if h.period_end else "",
            "create_time": h.create_time.strftime("%Y-%m-%d %H:%M:%S") if h.create_time else "",
            "state": 2,  # 2=已归档（与边缘历史页语义一致）
            "running": 0,
        })

    # 拼接进行中周期（实时表），period_start 取 last_reset_time/create_time
    live_qs = NodeStatisticAlarmModel.objects.filter(
        node_code=node_code, control_code=control_code)
    if task_name:
        live_qs = live_qs.filter(task_name=task_name)
    for cur in live_qs.order_by("-update_time"):
        rows.insert(0, {
            "id": "live_%d" % cur.id,
            "node_code": cur.node_code,
            "control_code": cur.control_code,
            "task_name": cur.task_name,
            "enter_num": cur.enter_num,
            "leave_num": cur.leave_num,
            "total_num": cur.total_num,
            "snap_url": cur.snap_url or "",
            "reset_strategy": cur.reset_strategy or "manual",
            "period_start": (cur.last_reset_time or cur.create_time).strftime("%Y-%m-%d %H:%M:%S") if (cur.last_reset_time or cur.create_time) else "",
            "period_end": "",
            "create_time": cur.update_time.strftime("%Y-%m-%d %H:%M:%S") if cur.update_time else "",
            "state": 0,  # 0=活跃/进行中
            "running": 1,
        })
    return True, "success", rows

def page_countHistory(request):
    """计数历史页面：某节点某布控的周期归档 + 进行中周期，趋势图+表格+删除+导出。"""
    params = f_parseGetParams(request)
    node_code = str(params.get("node_code", "")).strip()
    control_code = str(params.get("control_code", "")).strip()
    task_name = str(params.get("task_name", "")).strip()

    node_nickname = node_code
    try:
        n = NodeModel.objects.filter(code=node_code).first()
        if n:
            node_nickname = n.nickname
    except Exception as e:
        g_logger.warning("AlarmView.page_countHistory() load node error:%s" % str(e))

    context = {
        "settings": f_settingsReadData(),
        "page_title": _("计数历史"),
        "node_code": node_code,
        "control_code": control_code,
        "task_name": task_name,
        "node_nickname": node_nickname,
        "error": "" if (node_code and control_code) else _("缺少节点或布控参数"),
    }
    return render(request, 'app/alarm/count_history.html', context)

def api_openStatisticHistory(request):
    """计数历史列表（归档周期+进行中周期）。"""
    ret = False
    msg = _("未知错误")
    data = []
    if request.method == 'GET':
        __check_ret, __check_msg = f_checkRequestSafe(request)
        if __check_ret:
            ret, msg, data = _statisticHistoryQuery(request)
        else:
            msg = __check_msg
    else:
        msg = "request method not supported"
    res = {
        "code": 1000 if ret else 0,
        "msg": msg,
        "data": data,
    }
    return f_responseJson(res)

def api_openDeleteStatisticHistory(request):
    """删除单条计数历史（仅云端记录，id 形如 live_x 的进行中周期不可删）。"""
    ret = False
    msg = _("未知错误")
    if request.method == 'POST':
        __check_ret, __check_msg = f_checkRequestSafe(request)
        if __check_ret:
            params = f_parsePostParams(request)
            record_id = str(params.get("record_id", "")).strip()
            if not record_id or record_id.startswith("live_"):
                msg = _("无效的记录ID（进行中周期不可删除）")
            else:
                try:
                    obj = NodeStatisticHistoryModel.objects.filter(id=int(record_id)).first()
                    if obj is None:
                        msg = _("记录不存在")
                    else:
                        obj.delete()
                        ret = True
                        msg = _("删除成功")
                except Exception as e:
                    msg = _("删除失败") + ": %s" % str(e)
                    g_logger.error("AlarmView.openDeleteStatisticHistory() error:%s" % str(e))
        else:
            msg = __check_msg
    else:
        msg = "request method not supported"
    res = {"code": 1000 if ret else 0, "msg": msg}
    g_logger.info("AlarmView.openDeleteStatisticHistory() res:%s" % str(res))
    return f_responseJson(res)

def api_openExportStatisticHistory(request):
    """计数历史导出 Excel（openpyxl，与边缘 exportCountHistory 同风格）。"""
    if request.method != 'GET':
        return f_responseJson({"code": 0, "msg": "request method not supported"})
    __check_ret, __check_msg = f_checkRequestSafe(request)
    if not __check_ret:
        return f_responseJson({"code": 0, "msg": __check_msg})

    ret, msg, rows = _statisticHistoryQuery(request)
    if not ret:
        return f_responseJson({"code": 0, "msg": msg})
    if not rows:
        return f_responseJson({"code": 0, "msg": _("该布控暂无历史数据")})

    node_nickname = ""
    if rows:
        try:
            n = NodeModel.objects.filter(code=rows[0]["node_code"]).first()
            if n:
                node_nickname = n.nickname
        except Exception:
            pass

    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill
        from django.http import HttpResponse

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "计数历史"
        headers = ['ID', '节点', '任务名称', '布控代码', '进入数', '离开数', '总计',
                   '周期开始', '周期结束', '状态', '清零策略']
        ws.append(headers)
        header_fill = PatternFill(start_color="2A80EB", end_color="2A80EB", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')

        strategy_names = {"manual": "手动清零", "hourly": "每小时清零", "daily": "每日清零",
                          "weekly": "每周清零", "monthly": "每月清零"}
        for r in rows:
            state_text = "进行中" if r["running"] else "已归档"
            ws.append([
                r["id"] if isinstance(r["id"], int) else "-",
                "%s(%s)" % (node_nickname, r["node_code"]) if node_nickname else r["node_code"],
                r["task_name"],
                r["control_code"],
                r["enter_num"],
                r["leave_num"],
                r["total_num"],
                r["period_start"],
                r["period_end"] or "-",
                state_text,
                strategy_names.get(r["reset_strategy"], r["reset_strategy"]),
            ])
        for i, width in enumerate([10, 22, 20, 18, 10, 10, 10, 20, 20, 10, 12], 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

        filename = "计数历史_%s_%s.xlsx" % (r_ctrl if (r_ctrl := rows[0]["control_code"]) else "all",
                                           datetime.now().strftime("%Y%m%d_%H%M%S"))
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename
        wb.save(response)
        return response
    except ImportError:
        return f_responseJson({"code": 0, "msg": "缺少openpyxl库，请安装: pip install openpyxl"})
    except Exception as e:
        g_logger.error("AlarmView.openExportStatisticHistory() error:%s" % str(e))
        return f_responseJson({"code": 0, "msg": _("导出失败") + ": %s" % str(e)})

def api_openStatisticIndex(request):
    """计数告警列表（eai_node_statistic_alarm 全量，前端本地搜索）。"""
    ret = False
    msg = _("未知错误")
    data = []

    __check_ret, __check_msg = f_checkRequestSafe(request)
    if __check_ret:
        node_nickname_map = {}
        try:
            for n in NodeModel.objects.all():
                node_nickname_map[n.code] = n.nickname
        except Exception as e:
            g_logger.warning("AlarmView.openStatisticIndex() load nodes error:%s" % str(e))

        for s in NodeStatisticAlarmModel.objects.all().order_by("-update_time"):
            data.append({
                "id": s.id,
                "node_code": s.node_code,
                "node_nickname": node_nickname_map.get(s.node_code, s.node_code),
                "control_code": s.control_code,
                "task_name": s.task_name,
                "count": s.count,
                "enter_num": s.enter_num,
                "leave_num": s.leave_num,
                "total_num": s.total_num,
                "snap_url": s.snap_url,
                "reset_strategy": s.reset_strategy,
                "last_reset_time": s.last_reset_time.strftime("%Y-%m-%d %H:%M:%S") if s.last_reset_time else "",
                "update_time": s.update_time.strftime("%Y-%m-%d %H:%M:%S") if s.update_time else "",
            })
        ret = True
        msg = "success"
    else:
        msg = __check_msg

    res = {
        "code": 1000 if ret else 0,
        "msg": msg,
        "data": data
    }
    return f_responseJson(res)

def api_openResetCount(request):
    """
    计数清零（唯一回传例外）：转发边缘 alarms/openResetCount（Eai-Secret），
    边缘清零成功后云端同步清零 eai_node_statistic_alarm。
    """
    ret = False
    msg = _("未知错误")

    if request.method == 'POST':
        __check_ret, __check_msg = f_checkRequestSafe(request)
        if __check_ret:
            params = f_parsePostParams(request)
            g_logger.info("AlarmView.openResetCount() params:%s" % str(params))

            node_code = str(params.get('node_code', "")).strip()
            control_code = str(params.get('control_code', "")).strip()
            task_name = str(params.get('task_name', "")).strip()

            __node_ret, __node_msg, node = f_checkNode(node_code=node_code)
            if __node_ret:
                try:
                    import requests as _requests
                    headers = {
                        "User-Agent": PROJECT_UA,
                        "Content-Type": "application/json;",
                        "Eai-Secret": node.eai_safe
                    }
                    res = _requests.post(url='%s/alarms/openResetCount' % node.address,
                                         headers=headers, data=json.dumps(params), timeout=TIMEOUT)
                    if res.status_code == 200:
                        res_result = res.json()
                        if int(res_result.get("code", 0)) == 1000:
                            # 边缘清零成功 → 云端先归档旧周期再同步清零
                            now = datetime.now()
                            qs = NodeStatisticAlarmModel.objects.filter(
                                node_code=node_code, control_code=control_code)
                            if task_name:
                                qs = qs.filter(task_name=task_name)
                            _archiveStatistic(qs, now, "manual")
                            qs.update(count=0, enter_num=0, leave_num=0,
                                      last_reset_time=now, update_time=now)
                            ret = True
                            msg = "success"
                        else:
                            msg = res_result.get("msg") or _("边缘清零失败")
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
    g_logger.info("AlarmView.openResetCount() res:%s" % str(res))
    return f_responseJson(res)
def api_openIndex(request):
    ret = False
    msg = _("未知错误")

    top_msg = ""
    data = []
    pageData = {}
    __check_ret, __check_msg = f_checkRequestSafe(request)
    if __check_ret:
        params = f_parseGetParams(request)
        page = params.get('p', 1)
        page_size = params.get('ps', 10)
        drawType = str(params.get('drawType', "-1"))
        controlCode = str(params.get('controlCode', "-1"))
        streamCode = str(params.get('streamCode', "-1"))
        flowCode = str(params.get('flowCode', "-1"))
        # P3: 分类/节点/状态筛选（alarm_category: 0事件 1车牌 2人脸 3计数）
        alarmCategory = str(params.get('alarmCategory', "-1"))
        nodeCode = str(params.get('nodeCode', "-1"))
        state = str(params.get('state', "-1"))

        dateRange = str(params.get('dateRange'))

        startTimestamp = 0
        endTimestamp = 0
        try:
            dateRangeV = dateRange.split("to")
            if len(dateRangeV) == 2:
                startDate = dateRangeV[0].strip()
                endDate = dateRangeV[1].strip()
                startTimestamp = int(datetime.strptime(startDate, "%Y-%m-%d").timestamp())
                endTimestamp = int(datetime.strptime(endDate, "%Y-%m-%d").timestamp())
        except:
            pass

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

        search_fields = []
        if drawType != "-1":
            search_fields.append(" eai_node_alarm.draw_type = {field} ".format(field=int(drawType)))
        if controlCode != "-1":
            search_fields.append(" eai_node_alarm.control_code = '{field}' ".format(field=controlCode))
        if streamCode != "-1":
            search_fields.append(" eai_node_alarm.stream_code = '{field}' ".format(field=streamCode))
        if flowCode != "-1":
            search_fields.append(" eai_node_alarm.flow_code = '{field}' ".format(field=flowCode))
        if alarmCategory != "-1":
            search_fields.append(" eai_node_alarm.alarm_category = {field} ".format(field=int(alarmCategory)))
        if nodeCode != "-1":
            search_fields.append(" eai_node_alarm.node_code = '{field}' ".format(field=nodeCode))
        if state != "-1":
            search_fields.append(" eai_node_alarm.state = {field} ".format(field=int(state)))

        if startTimestamp > 0 and endTimestamp > 0:
            search_fields.append(
                " eai_node_alarm.create_timestamp>={startTimestamp} and eai_node_alarm.create_timestamp<={endTimestamp} ".format(
                    startTimestamp=startTimestamp, endTimestamp=endTimestamp))
        # 拼接where
        where_count = "where eai_node_alarm.state!=5 "
        if len(search_fields) > 0:
            where_count += " and " + "and".join(search_fields)

        where_unread_count = "where eai_node_alarm.state=0 "
        if len(search_fields) > 0:
            where_unread_count += " and " + "and".join(search_fields)

        # 节点昵称字典
        node_nickname_map = {}
        try:
            for n in NodeModel.objects.all():
                node_nickname_map[n.code] = n.nickname
        except Exception as e:
            g_logger.warning("AlarmView.openIndex() load nodes error:%s" % str(e))

        # 查询满足where条件的数量
        count = g_database.select("select count(id) as count from eai_node_alarm %s" % where_count)
        count = int(count[0]["count"])

        unread_count = 0
        if count > 0:
            # 查询满足where的数据
            skip = (page - 1) * page_size
            __data = g_database.select("select eai_node_alarm.* from eai_node_alarm %s order by eai_node_alarm.id desc limit %d,%d " % (
                where_count, skip,page_size))

            for d in __data:
                video_count = d["video_count"]
                if video_count > 0:
                    videoUrl = d["video_path"]
                    # 兼容老数据相对路径与 push 完整地址
                    if videoUrl and not videoUrl.startswith(("http://", "https://", "/storage/")):
                        videoUrl = g_config.storageDir_www + videoUrl
                else:
                    videoUrl = ""

                image_count = d["image_count"]
                if image_count > 0:
                    imageUrl = d["image_path"]
                    if imageUrl and not imageUrl.startswith(("http://", "https://", "/storage/")):
                        imageUrl = g_config.storageDir_www + imageUrl
                else:
                    imageUrl = "/static/images/720p.jpg"

                data.append({
                    "id": d["id"],
                    "code": d["code"],
                    "event_id": d.get("event_id", ""),
                    "node_code": d["node_code"],
                    "node_nickname": node_nickname_map.get(d["node_code"], d["node_code"]),
                    "video_count": video_count,
                    "videoUrl": videoUrl,
                    "image_count": image_count,
                    "imageUrl": imageUrl,
                    "desc": d["desc"],
                    "create_time": d["create_time"],
                    "create_time_str": d["create_time"].strftime("%Y-%m-%d %H:%M:%S"),
                    "state": d["state"],
                    "risk_level": d.get("risk_level", 0),
                    "task_name": d.get("task_name", ""),
                    "deal_info": d.get("deal_info", ""),
                    "alarm_category": d.get("alarm_category", 0),
                    "control_code": d["control_code"],
                    "flow_code": d["flow_code"],
                    "flow_name": d["flow_name"],
                    "main_plate_no": d.get("main_plate_no", ""),
                    "main_track_max_custom_code": d.get("main_track_max_custom_code", ""),
                })
            # 查询满足where条件的未读数量
            unread_count = g_database.select("select count(id) as count from eai_node_alarm %s" % where_unread_count)
            if len(unread_count) > 0:
                unread_count = int(unread_count[0]["count"])
            else:
                unread_count = 0

        page_num = int(count / page_size)  # 总页数
        if count % page_size > 0:
            page_num += 1
        pageLabels = buildPageLabels(page=page, page_num=page_num)
        pageData = {
            "page": page,
            "page_size": page_size,
            "page_num": page_num,
            "count": count,
            "pageLabels": pageLabels
        }
        if count > 0:
            top_msg = _("总计%d条，未处理%d条") % (count, unread_count)
        else:
            top_msg = _("暂无数据")

        ret = True
        msg = "success"
    else:
        msg = __check_msg

    res = {
        "code": 1000 if ret else 0,
        "msg": msg,
        "data": data,
        "pageData": pageData,
        "top_msg": top_msg
    }
    return f_responseJson(res)

# description: 获取报警信息
def api_openInfo(request):
    ret = False
    msg = _("未知错误")
    info = {}
    if request.method == 'GET':
        __check_ret, __check_msg = f_checkRequestSafe(request)
        if __check_ret:
            params = f_parseGetParams(request)
            g_logger.info("AlarmView.openInfo() params:%s" % str(params))

            alarm_code = params.get("code", "")
            alarm_info = f_getAlarmInfoByCode(alarm_code=alarm_code)
            if alarm_info:
                info = alarm_info
                ret = True
                msg = "success"
            else:
                msg = "the data does not exist"
        else:
            msg = __check_msg
    else:
        msg = "request method not supported"

    res = {
        "code": 1000 if ret else 0,
        "msg": msg,
        "info": info
    }
    g_logger.info("AlarmView.openInfo() res:%s" % str(res))

    return f_responseJson(res)

def api_openHandle(request):
    ret = False
    msg = _("未知错误")

    if request.method == 'POST':
        __check_ret, __check_msg = f_checkRequestSafe(request)
        if __check_ret:
            params = f_parsePostParams(request)
            g_logger.info("AlarmView.openHandle() params:%s" % str(params))

            alarm_ids_str = params.get("alarm_ids_str", "")
            handle = params.get("handle", None)
            if handle == "deleteAll": # 全部删除（逻辑删除）
                data = g_database.select("select count(1) as count from eai_node_alarm where state!=5")
                count = data[0]["count"]
                if count > 0:
                    g_database.execute("update eai_node_alarm set state = 5")
                    msg = "success"
                    ret = True
                else:
                    msg = _("暂无待删除数据")
            elif handle == "clearCache":
                # 清理报警缓存
                ret, msg = AlarmUtils(g_logger, g_database, g_config.storageDir).clearAlarm()
            elif handle == "delete":  # 批量删除（逻辑删除）

                alarm_ids = alarm_ids_str.split(",")
                if len(alarm_ids) > 0:
                    success_count = 0
                    error_count = 0
                    for alarm_id in alarm_ids:
                        alarm = NodeAlarmModel.objects.filter(id=alarm_id)
                        if len(alarm) > 0:
                            alarm = alarm[0]
                            alarm.state = 5
                            alarm.save()
                            success_count += 1
                        else:
                            error_count += 1

                    msg = _("成功%d条，失败%d条") % (success_count, error_count)
                    ret = True
                else:
                    msg = _("请至少选择一条数据")
            else:
                # 处理告警：state 2已处理 / 3误报（新语义，仅本地改库不回传节点）
                try:
                    handle_state = int(handle)
                except Exception:
                    handle_state = -1
                if handle_state in (2, 3):
                    alarm_ids = [i for i in alarm_ids_str.split(",") if i]
                    if len(alarm_ids) > 0:
                        success_count = 0
                        error_count = 0
                        deal_info = str(params.get("deal_info", ""))[:500]
                        for alarm_id in alarm_ids:
                            alarm = NodeAlarmModel.objects.filter(id=alarm_id).first()
                            if alarm:
                                alarm.state = handle_state
                                alarm.deal_info = deal_info
                                alarm.last_update_time = datetime.now()
                                alarm.save(update_fields=["state", "deal_info", "last_update_time"])
                                success_count += 1
                            else:
                                error_count += 1
                        msg = _("成功%d条，失败%d条") % (success_count, error_count)
                        ret = True
                    else:
                        msg = _("请至少选择一条数据")
                else:
                    msg = _("不支持的操作类型")
        else:
            msg = __check_msg
    else:
        msg = "request method not supported"
    res = {
        "code": 1000 if ret else 0,
        "msg": msg
    }
    g_logger.info("AlarmView.openHandle() res:%s" % str(res))
    return f_responseJson(res)

def api_openExport(request):
    """告警导出 CSV（按当前筛选条件：分类/节点/状态/日期，与 openIndex 一致）。"""
    ret = False
    msg = _("未知错误")
    info = {}

    if request.method == 'POST':
        __check_ret, __check_msg = f_checkRequestSafe(request)
        if __check_ret:
            params = f_parsePostParams(request)
            g_logger.info("AlarmView.openExport() params:%s" % str(params))

            # ── 筛选条件（与 openIndex 保持一致） ──
            alarmCategory = str(params.get('alarmCategory', "-1"))
            nodeCode = str(params.get('nodeCode', "-1"))
            state = str(params.get('state', "-1"))
            dateRange = str(params.get('dateRange', ""))

            startTimestamp = 0
            endTimestamp = 0
            try:
                dateRangeV = dateRange.split("to")
                if len(dateRangeV) == 2:
                    startTimestamp = int(datetime.strptime(dateRangeV[0].strip(), "%Y-%m-%d").timestamp())
                    endTimestamp = int(datetime.strptime(dateRangeV[1].strip(), "%Y-%m-%d").timestamp())
            except Exception:
                pass

            search_fields = []
            if alarmCategory not in ("-1", ""):
                search_fields.append(" alarm_category = %s " % int(alarmCategory))
            if nodeCode not in ("-1", ""):
                search_fields.append(" node_code = '%s' " % nodeCode)
            if state not in ("-1", ""):
                search_fields.append(" state = %s " % int(state))
            if startTimestamp > 0 and endTimestamp > 0:
                search_fields.append(" create_timestamp >= %d and create_timestamp <= %d " % (startTimestamp, endTimestamp))

            where = "where state != 5 "
            if search_fields:
                where += " and " + "and".join(search_fields)

            # ── 节点昵称字典 ──
            node_nickname_map = {}
            try:
                for n in NodeModel.objects.all():
                    node_nickname_map[n.code] = n.nickname
            except Exception as e:
                g_logger.warning("AlarmView.openExport() load nodes error:%s" % str(e))

            # ── 查询并生成 CSV（上限 10000 条防滥用） ──
            rows = g_database.select(
                "select * from eai_node_alarm %s order by id desc limit 10000" % where)

            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([_("告警编号"), _("事件ID"), _("所属节点"), _("告警分类"), _("算法任务"), _("布控编号"),
                             _("告警描述"), _("风险等级"), _("状态"), _("处理信息"), _("车牌号"), _("告警时间")])
            for d in rows:
                writer.writerow([
                    d.get("code", ""),
                    d.get("event_id", ""),
                    "%s(%s)" % (node_nickname_map.get(d.get("node_code", ""), d.get("node_code", "")), d.get("node_code", "")),
                    ALARM_CATEGORY_NAMES.get(d.get("alarm_category", 0), _("事件告警")),
                    d.get("task_name", "") or d.get("flow_name", ""),
                    d.get("control_code", ""),
                    d.get("desc", ""),
                    ALARM_RISK_NAMES.get(d.get("risk_level", 0), _("低风险")),
                    ALARM_STATE_NAMES.get(d.get("state", 0), _("未读")),
                    d.get("deal_info", "") or "",
                    d.get("main_plate_no", "") or "",
                    d.get("create_time", "") or "",
                ])

            # 写入 BOM 便于 Excel 识别 UTF-8
            csv_content = "\ufeff" + output.getvalue()

            # ── 存临时文件返回下载地址（与静态存储目录复用） ──
            filename = "alarm_export_%s.csv" % datetime.now().strftime("%Y%m%d%H%M%S")
            rel_path = "alarm/export/%s" % filename
            abs_dir = os.path.join(g_config.storageDir, "alarm/export")
            if not os.path.exists(abs_dir):
                os.makedirs(abs_dir)
            with open(os.path.join(abs_dir, filename), "w", encoding="utf-8") as f:
                f.write(csv_content)

            ret = True
            msg = "success"
            info = {
                "count": len(rows),
                # storageDir_www = "/storage/access?filename="，拼相对路径（与告警图片/视频一致）
                "url": "%s%s" % (g_config.storageDir_www, rel_path),
            }
        else:
            msg = __check_msg
    else:
        msg = "request method not supported"

    res = {
        "code": 1000 if ret else 0,
        "msg": msg,
        "info": info
    }
    g_logger.info("AlarmView.openExport() res:%s" % str(res))
    return f_responseJson(res)


# ─────────────────── P3: 边缘推送上行链路（免登录，验签准入） ───────────────────

# 告警文件扩展名白名单（存储访问层 storage/access 同步支持）
PUSH_UPLOAD_FILE_EXT = (".jpg", ".jpeg", ".png", ".mp4", ".wav", ".avi")
# event_type(task_name) → alarm_category：0事件 1车牌 2人脸 3计数
ALARM_CATEGORY_MAP = {
    "carplate_task": 1,
    "face_task": 2,
}

def f_alarmCategoryOf(task_name, event_type=""):
    """按算法任务名归类告警：0事件 1车牌 2人脸 3计数。"""
    key = (task_name or event_type or "").strip()
    if key in ALARM_CATEGORY_MAP:
        return ALARM_CATEGORY_MAP[key]
    if key.endswith("carplate"):
        return 1
    if key.endswith("face"):
        return 2
    # 计数类：object_task 下的统计任务由边缘推送时显式带 count 字段归类
    return 0

def api_openUploadFile(request):
    """
    边缘告警媒体文件上传（multipart）。
    验签 payload 固定为 {"msg_type":"upload"}（与边缘 _upload_file 签名一致）。
    存储到 storage/alarm_upload/{yyyyMMdd}/，返回可访问 URL（/storage/access?filename=...）。
    """
    ret = False
    msg = _("未知错误")
    url = ""

    if request.method == 'POST':
        sign_payload = {"msg_type": "upload"}
        ok, sign_msg = f_verifyPushSign(request, sign_payload)
        if ok:
            upload_file = request.FILES.get("file")
            if upload_file is None:
                msg = "missing file field"
            else:
                filename = os.path.basename(upload_file.name or "")
                ext = os.path.splitext(filename)[1].lower()
                if not ext or ext not in PUSH_UPLOAD_FILE_EXT:
                    msg = "unsupported file type: %s" % ext
                else:
                    try:
                        day_dir = datetime.now().strftime("%Y%m%d")
                        save_dir = os.path.join(g_config.storageAlarmDir, "upload", day_dir)
                        if not os.path.exists(save_dir):
                            os.makedirs(save_dir)
                        # 防冲突文件名：日期_随机串.扩展名
                        new_name = "%s_%s%s" % (
                            datetime.now().strftime("%Y%m%d%H%M%S"), gen_random_code_s("f"), ext)
                        save_path = os.path.join(save_dir, new_name)
                        with open(save_path, "wb") as f:
                            for chunk in upload_file.chunks():
                                f.write(chunk)
                        # 存相对 storageDir 的路径，URL 走存储访问层
                        rel_path = os.path.relpath(save_path, g_config.storageDir).replace("\\", "/")
                        url = "%s%s" % (g_config.storageDir_www, rel_path)
                        ret = True
                        msg = "success"
                    except Exception as e:
                        msg = "save file error: %s" % str(e)
                        g_logger.error("AlarmView.openUploadFile() save error:%s" % str(e))
        else:
            msg = "verify sign failed: %s" % sign_msg
    else:
        msg = "request method not supported"

    res = {
        "code": 1000 if ret else 0,
        "msg": msg,
        "data": {"url": url}
    }
    g_logger.info("AlarmView.openUploadFile() res:%s" % str(res))
    return f_responseJson(res)

def api_openPush(request):
    """
    边缘告警推送接收（JSON，格式以边缘 push_alarm_to_cloud 为准）。
    msg_type: alarm（告警）/ statistic（计数统计）/ statistic_reset（清零通知）
    """
    ret = False
    msg = _("未知错误")

    if request.method == 'POST':
        payload, raw_body = f_parsePushJsonBody(request)
        if payload is None:
            msg = "invalid json body"
        else:
            ok, sign_msg = f_verifyPushSign(request, payload)
            if not ok:
                msg = "verify sign failed: %s" % sign_msg
            else:
                msg_type = str(payload.get("msg_type") or "alarm")
                if msg_type == "alarm":
                    ret, msg = _pushHandleAlarm(payload)
                elif msg_type == "statistic":
                    ret, msg = _pushHandleStatistic(payload)
                elif msg_type == "statistic_reset":
                    ret, msg = _pushHandleStatisticReset(payload)
                else:
                    msg = "unsupported msg_type: %s" % msg_type
    else:
        msg = "request method not supported"

    res = {
        "code": 1000 if ret else 0,
        "msg": msg
    }
    g_logger.info("AlarmView.openPush() res:%s" % str(res))
    return f_responseJson(res)

def _pushRouteNode(payload):
    """
    device_info.device_id → eai_node.code 路由。
    :return: (node, error_msg) —— node 为 None 时 error_msg 说明原因
    """
    device_info = payload.get("device_info") or {}
    if not isinstance(device_info, dict):
        device_info = {}
    device_id = str(device_info.get("device_id") or "").strip()
    if not device_id:
        return None, "missing device_info.device_id"
    node = NodeModel.objects.filter(code=device_id).first()
    if node is None:
        return None, "node not found: %s" % device_id
    if node.state != 1:
        g_logger.warning("AlarmView.openPush() node offline but accept push: %s" % device_id)
    return node, ""

def _pushHandleAlarm(payload):
    """msg_type=alarm：落库 eai_node_alarm。"""
    # 1. 节点路由
    node, err = _pushRouteNode(payload)
    if node is None:
        return False, "route failed: %s" % err

    event_id = str(payload.get("event_id") or "").strip()
    if not event_id:
        return False, "missing event_id"

    # 2. 幂等：event_id 唯一，重复推送直接成功
    if NodeAlarmModel.objects.filter(event_id=event_id).exists():
        return True, "duplicate event_id, skip"

    # 3. 字段映射
    task_name = str(payload.get("task_name") or payload.get("event_type") or "")
    control_code = str(payload.get("control_code") or "")
    description = str(payload.get("description") or "")
    image_url = str(payload.get("image_url") or "")
    video_url = str(payload.get("video_url") or "")

    # 状态映射：边缘仅推 0/1/2/3；4/5/6 复检态按 1（未处理）兜底
    try:
        push_state = int(payload.get("state", 0))
    except Exception:
        push_state = 0
    if push_state in (0, 1, 2, 3):
        state = push_state
    else:
        state = 1

    try:
        risk_level = int(payload.get("risk_level") or 0)
    except Exception:
        risk_level = 0
    if risk_level not in (0, 1, 2):
        risk_level = 0

    detect_objects = payload.get("detect_objects")
    if isinstance(detect_objects, (list, dict)):
        detect_objs = json.dumps(detect_objects, ensure_ascii=False)
    else:
        detect_objs = str(detect_objects or "")

    # 事件时间：yyyy-MM-dd HH:mm:ss → 时间戳/DateTime
    event_time_str = str(payload.get("event_time") or "").strip()
    create_timestamp = int(time.time())
    create_dt = datetime.now()
    if event_time_str:
        try:
            create_dt = datetime.strptime(event_time_str, "%Y-%m-%d %H:%M:%S")
            create_timestamp = int(create_dt.timestamp())
        except Exception:
            pass

    alarm_category = payload.get("alarm_category")
    if alarm_category is None:
        alarm_category = f_alarmCategoryOf(task_name, str(payload.get("event_type") or ""))
    try:
        alarm_category = int(alarm_category)
    except Exception:
        alarm_category = 0
    if alarm_category not in (0, 1, 2, 3):
        alarm_category = 0

    device_info = payload.get("device_info") or {}
    if not isinstance(device_info, dict):
        device_info = {}

    # 复用现有页码/列表逻辑字段
    try:
        now = datetime.now()
        max_sort = NodeAlarmModel.objects.filter().order_by("-sort").values_list("sort", flat=True).first()
        sort = (max_sort or 0) + 1
        alarm = NodeAlarmModel(
            sort=sort,
            code=gen_random_code_s("alarm"),
            event_id=event_id,
            draw_type=0,
            flag="push",
            node_code=node.code,
            control_code=control_code,
            desc=(description or "边缘推送告警")[:200],
            video_path=video_url,
            video_count=1 if video_url else 0,
            image_path=image_url,
            image_count=1 if image_url else 0,
            other_image_count=0,
            level=risk_level,  # 报警级别与风险等级对齐（0低1中2高）
            risk_level=risk_level,
            state=state,
            is_check=0,
            deal_info="",
            alarm_category=alarm_category,
            review_remark="",
            stream_app="",
            stream_name="",
            stream_code="",
            flow_mode=0,
            flow_code="",
            flow_name="",
            task_name=task_name[:200],
            detect_objs=detect_objs,
            main_plate_color=0,
            main_plate_type=0,
            main_plate_no="",
            main_track_max_code="",
            main_track_max_custom_code="",
            main_track_max_similary=0,
            expand1=str(device_info.get("device_name") or "")[:200],
            expand2=str(device_info.get("device_ip") or "")[:200],
            create_time=now,
            create_timestamp=create_timestamp,
            last_update_time=now,
        )
        alarm.save()
        return True, "success"
    except Exception as e:
        g_logger.error("AlarmView.openPush() save alarm error:%s" % str(e))
        return False, "save alarm error: %s" % str(e)

def _pushHandleStatistic(payload):
    """msg_type=statistic：落库/更新 eai_node_statistic_alarm。"""
    node, err = _pushRouteNode(payload)
    if node is None:
        return False, "route failed: %s" % err

    control_code = str(payload.get("control_code") or "").strip()
    task_name = str(payload.get("task_name") or "").strip()
    if not control_code or not task_name:
        return False, "missing control_code/task_name"

    def _int_field(key):
        try:
            return int(payload.get(key) or 0)
        except Exception:
            return 0

    count = _int_field("count")
    enter_num = _int_field("enter_num")
    leave_num = _int_field("leave_num")
    total_num = _int_field("total_num")
    snap_url = str(payload.get("snap_url") or "")[:500]
    reset_strategy = str(payload.get("reset_strategy") or "manual")[:20]
    now = datetime.now()

    obj = NodeStatisticAlarmModel.objects.filter(
        node_code=node.code, control_code=control_code, task_name=task_name).first()
    try:
        if obj:
            obj.count = count
            obj.enter_num = enter_num
            obj.leave_num = leave_num
            obj.total_num = total_num
            if snap_url:
                obj.snap_url = snap_url
            obj.reset_strategy = reset_strategy
            obj.update_time = now
            obj.save()
        else:
            NodeStatisticAlarmModel.objects.create(
                node_code=node.code,
                control_code=control_code,
                task_name=task_name,
                count=count,
                enter_num=enter_num,
                leave_num=leave_num,
                total_num=total_num,
                snap_url=snap_url,
                reset_strategy=reset_strategy,
                update_time=now,
                create_time=now,
            )
        return True, "success"
    except Exception as e:
        g_logger.error("AlarmView.openPush() save statistic error:%s" % str(e))
        return False, "save statistic error: %s" % str(e)

def _pushHandleStatisticReset(payload):
    """msg_type=statistic_reset：边缘周期清零通知，云端归档旧周期后清零。"""
    node, err = _pushRouteNode(payload)
    if node is None:
        return False, "route failed: %s" % err

    control_code = str(payload.get("control_code") or "").strip()
    task_name = str(payload.get("task_name") or "").strip()
    now = datetime.now()

    qs = NodeStatisticAlarmModel.objects.filter(node_code=node.code)
    if control_code:
        qs = qs.filter(control_code=control_code)
    if task_name:
        qs = qs.filter(task_name=task_name)
    if not control_code and not task_name:
        return False, "missing control_code/task_name"

    try:
        # 清零前归档旧周期汇总到历史表
        archived = _archiveStatistic(qs, now, "reset")
        updated = qs.update(
            count=0, enter_num=0, leave_num=0,
            last_reset_time=now, update_time=now)
        return True, "success (%d rows, archived %d)" % (updated, archived)
    except Exception as e:
        g_logger.error("AlarmView.openPush() reset statistic error:%s" % str(e))
        return False, "reset statistic error: %s" % str(e)

def _archiveStatistic(qs, now, reason=""):
    """
    清零前把实时表当前值归档为一条周期历史。
    period_start 取实时表 last_reset_time（上次清零时间），无则取 create_time。
    :param qs: NodeStatisticAlarmModel 的 filter QuerySet
    :param now: 归档时间（= period_end）
    :return: 归档条数
    """
    archived = 0
    for cur in qs:
        # 全 0 的周期无归档意义（刚清零/从未计数）
        if not (cur.count or cur.enter_num or cur.leave_num or cur.total_num):
            continue
        period_start = cur.last_reset_time or cur.create_time
        try:
            NodeStatisticHistoryModel.objects.create(
                node_code=cur.node_code,
                control_code=cur.control_code,
                task_name=cur.task_name,
                enter_num=cur.enter_num,
                leave_num=cur.leave_num,
                # total 兜底：边缘语义 total = enter + leave，旧数据/缺推时补算
                total_num=cur.total_num or (cur.enter_num + cur.leave_num),
                snap_url=cur.snap_url or "",
                reset_strategy=cur.reset_strategy or "manual",
                period_start=period_start,
                period_end=now,
            )
            archived += 1
        except Exception as e:
            g_logger.error("AlarmView._archiveStatistic() error:%s" % str(e))
    if archived > 0:
        g_logger.info("AlarmView._archiveStatistic() reason=%s archived=%d" % (reason, archived))
    return archived
