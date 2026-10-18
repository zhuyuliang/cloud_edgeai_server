from app.views.ViewsBase import *
from app.models import *
from app.utils.Settings import UserSettings
from app.utils.Utils import gen_dateArray
from django.shortcuts import render
from app.utils.OSSystem import OSSystem
from django.utils.translation import gettext as _


def index(request):
    context = {
        "settings": f_settingsReadData()
    }
    return render(request, 'app/index.html', context)

def dashboard(request):
    context = {
        "settings": f_settingsReadData()
    }
    params = f_parseGetParams(request)
    g_logger.info("StreamView.multiplayer() params:%s" % str(params))

    # 数据库的视频流数据转字典格式
    db_streams = f_dbReadStreamData()
    db_stream_dict = {}  # 数据库
    for d in db_streams:
        app_name = "{app}_{name}".format(app=d["app"], name=d["name"])
        db_stream_dict[app_name] = d

    # 在线视频流转字典格式
    online_group_dict = {}
    online_data = g_zlm.getMediaList()
    for d in online_data:
        app = d["app"]
        name = d["name"]
        app_name = d["an"]

        if app == "live" or app == "rtp":  # 只获取源视频
            f = db_stream_dict.get(app_name)  # 数据库查到的数据
            if f:
                d["source_type"] = 1  # 来自数据库
                d["source_nickname"] = f["nickname"]
            else:
                d["source_type"] = 0  # 来自推流
                d["source_nickname"] = "{app}/{name}".format(app=app, name=name)
            if not online_group_dict.get(app, None):
                online_group_dict[app] = []
            online_group_dict[app].append(d)

    # 添加算法流选项
    try:
        controls = ControlModel.objects.filter(state=1)
    except NameError:
        controls = []  # 云端无 av_control 表（布控在节点侧），降级为空算法流组
    analyzer_streams = []
    for control in controls:
        if control.state == 1:

            analyzer_app = "analyzer"
            analyzer_name = control.code
            analyzer_stream_code = "%s_%s" % (analyzer_app, analyzer_name)

            wsMp4Url = g_zlm.get_wsMp4Url(analyzer_app, analyzer_name)
            d = {
                'code': analyzer_stream_code,
                "app": analyzer_app,
                "name": analyzer_name,
                "video": "",
                "video_codec_name": "",
                "video_width": 0,
                "video_height": 0,
                "audio": "",
                "videoUrl": wsMp4Url,
                "wsHost": g_zlm.get_wsHost(),
                "wsMp4Url": wsMp4Url,
            }
            app_name = "%s_%s" % (control.stream_app, control.stream_name)
            f = db_stream_dict.get(app_name)  # 数据库查到的数据
            if f:
                d["source_type"] = 1  # 来自数据库
                d["source_nickname"] = f["nickname"]
            else:
                d["source_type"] = 0  # 来自推流
                d["source_nickname"] = "%s/%s" % (control.stream_app, control.stream_name)

            analyzer_streams.append(d)

    # 调整结构
    group_streams = []
    for group_name, streams in online_group_dict.items():
        group_streams.append({
            "group_name": group_name,
            "group_name_ch": f_replaceGroupName(group_name),
            "streams": streams
        })

    group_name = "analyzer"
    group_streams.append({
        "group_name": group_name,
        "group_name_ch": f_replaceGroupName(group_name),
        "streams": analyzer_streams
    })

    context["group_streams"] = group_streams
    try:
        context["uploadAudioDir_www"] = g_config.uploadAudioDir_www
    except AttributeError:
        context["uploadAudioDir_www"] = g_config.storageDir_www  # 云端无独立报警音频目录，复用存储访问前缀

    g_logger.info("StreamView.multiplayer() context:%s" % str(context))
    return render(request, 'app/dashboard.html', context)

def api_updateDashboardData(request):
    ret = False
    msg = _("未知错误")

    if request.method == 'POST':
        params = f_parsePostParams(request)
        g_logger.info("IndexView.updateDashboardData() params:%s" % str(params))
        gridVideoCount = int(params.get("gridVideoCount",0))
        gridVideoUrls = params.get("gridVideoUrls","")
        try:
            gridVideoUrlArray = gridVideoUrls.split("#")
            if gridVideoCount > 0 and gridVideoCount == len(gridVideoUrlArray):
                pass
            else:
                raise Exception(_("请求参数不正确"))

            user_settings = UserSettings(logger=g_logger)
            user_settings.add(user_id=f_sessionReadUserId(request),handle="dashboard",content=gridVideoUrls)

            ret = True
            msg = _("保存成功")

        except Exception as e:
            msg = str(e)
    else:
        msg = "request method not supported"
    res = {
        "code": 1000 if ret else 0,
        "msg": msg
    }
    g_logger.info("IndexView.updateDashboardData() res:%s" % str(res))
    return f_responseJson(res)

def api_getDashboardData(request):
    ret = False
    msg = _("未知错误")
    info = {
    }

    if request.method == 'GET':
        params = f_parseGetParams(request)
        # g_logger.info("IndexView.getDashboardData() params:%s" % str(params))
        alarm_rank_size = int(params.get("alarm_rank_size",8))
        alarm_size = int(params.get("alarm_size",10))

        now_date = datetime.now()
        now_ymd = "%04d%02d%02d" % (now_date.year, now_date.month, now_date.day)

        start_date = (now_date - timedelta(days=6))
        end_date = now_date
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp()) + 120
        data = g_database.select("select id,code,state,flow_code,flow_name,stream_code,image_path,image_count,create_time from eai_node_alarm where state!=5 and create_timestamp>={start_timestamp} and create_timestamp<={end_timestamp} order by id desc".format(
                    start_timestamp=start_timestamp, end_timestamp=end_timestamp))

        # 今日告警总数
        todayAlarmTotalCount = 0
        # 今日告警未处理总数
        todayAlarmUnHandleCount = 0
        # 今日告警已处理总数
        todayAlarmHandleCount = 0

        # 最近7天告警数据
        last7DayDateDict = gen_dateArray(start_date=start_date, end_date=end_date,listType=False)
        for d in data:
            create_time = d["create_time"]
            state = int(d.get("state",0))

            ymd = "%04d%02d%02d" % (create_time.year, create_time.month, create_time.day)
            if ymd == now_ymd:
                if state == 0:
                    todayAlarmTotalCount +=1
                    todayAlarmUnHandleCount +=1
                elif state == 1 or state == 2:
                    todayAlarmTotalCount +=1
                    todayAlarmHandleCount +=1

            f = last7DayDateDict.get(ymd)
            if f:
                last7DayDateDict[ymd]["count"] = f["count"] +1

        last7DayChartData = []
        for d in last7DayDateDict.values():
            new_d = {
                "x":d["timestamp"],
                "y":d["count"]
            }
            last7DayChartData.append(new_d)

        # 最近7天告警类型排行
        last7DayRankData = []
        flowData = f_dbReadAlgorithmFlowData()
        flowDict = {}
        for d in flowData:
            flowDict[d["code"]] = {
                "code":d["code"],
                "name":d["name"],
                "count":0
            }
        for d in data:
            flow_code = d["flow_code"]
            f = flowDict.get(flow_code)
            if f:
                flowDict[flow_code]["count"] = f["count"] + 1

        rankData = sorted(flowDict.values(),key=lambda x:x["count"],reverse=True)
        last7DayRankData = rankData[:alarm_rank_size] # 暂定查询前8条

        # 查询视频流数量
        streamData = f_dbReadStreamData()
        streamDict = {}
        streamTotalCount = 0
        streamOnlineCount = 0
        for d in streamData:
            streamDict[d["code"]] = d
            streamTotalCount += 1
            forward_state = int(d["forward_state"])
            if forward_state == 1:
                streamOnlineCount +=1

        # 查询报警数据
        alarmData = []
        for d in data:
            code = d["code"]
            flow_name = d["flow_name"]
            image_path = d["image_path"]
            image_count = d["image_count"]
            state = d["state"]
            stream_code = d["stream_code"]
            create_time = d["create_time"]
            f = streamDict.get(stream_code)
            if f:
                imageUrl = g_config.storageDir_www + image_path
                alarmData.append({
                    "code":code,
                    "flow_name": flow_name,
                    "image_path":imageUrl,
                    "image_count":image_count,
                    "imageUrl":imageUrl,
                    "state":state,
                    "stream_code": stream_code,
                    "stream_nickname": f["nickname"],
                    "create_time_str": create_time.strftime("%Y-%m-%d %H:%M")
                })
            if len(alarmData) == alarm_size:
                break


        info["last7DayChartData"] = last7DayChartData
        info["last7DayRankData"] = last7DayRankData
        info["todayAlarmTotalCount"] = todayAlarmTotalCount
        info["todayAlarmUnHandleCount"] = todayAlarmUnHandleCount
        info["todayAlarmHandleCount"] = todayAlarmHandleCount
        info["streamTotalCount"] = streamTotalCount
        info["streamOnlineCount"] = streamOnlineCount
        info["alarmData"] = alarmData

        ret = True
        msg = "success"

    else:
        msg = "request method not supported"
    res = {
        "code": 1000 if ret else 0,
        "msg": msg,
        "info": info
    }
    # g_logger.info("IndexView.getDashboardData() res:%s" % str(res))
    return f_responseJson(res)

def api_getDashboardPlayerData(request):
    ret = False
    msg = _("未知错误")
    info = {
    }

    if request.method == 'GET':
        params = f_parseGetParams(request)
        # g_logger.info("IndexView.getDashboardPlayerData() params:%s" % str(params))

        # 读取视频播放记忆
        user_settings = UserSettings(logger=g_logger)
        gridVideoUrls = user_settings.get(user_id=f_sessionReadUserId(request), handle="dashboard")
        if gridVideoUrls:
            gridVideoUrlArray = gridVideoUrls.split("#")
        else:
            gridVideoUrlArray = []
        gridVideoCount = len(gridVideoUrlArray)

        info["gridVideoCount"] = gridVideoCount
        info["gridVideoUrlArray"] = gridVideoUrlArray

        ret = True
        msg = "success"

    else:
        msg = "request method not supported"
    res = {
        "code": 1000 if ret else 0,
        "msg": msg,
        "info": info
    }
    # g_logger.info("IndexView.getDashboardPlayerData() res:%s" % str(res))
    return f_responseJson(res)


def api_getNewAlarm(request):
    ret = False
    msg = _("未知错误")

    info = {}
    alarm = g_database.select(
        "select * from eai_node_alarm where is_check=0 and state=0 order by id desc limit 1")

    if len(alarm) > 0:
        alarm = alarm[0]

        create_time = alarm["create_time"]
        now = datetime.now()

        # print(cur_date,create_time,(cur_date - create_time).total_seconds())
        if (now - create_time).total_seconds() <= getattr(g_config, "checkAlarmMaxDuration", 120):  # 2分钟内的报警才会被检测  1分钟=60秒
            try:
                control_code = alarm["control_code"]
                control = ControlModel.objects.get(code=control_code)
                audio = AudioModel.objects.get(code=control.audio_code)
                alarm["create_time_str"] = alarm["create_time"].strftime("%Y-%m-%d %H:%M:%S")
                info["alarm"] = alarm
                info["audio_path"] = audio.audio_path

                # 获取并拼接所有图片start
                imageUrlArray = []

                image_count = alarm["image_count"]
                if image_count > 0:
                    image_path = alarm["image_path"]  # alarm/control823181fa71/20240810/094055/1/20240810094055.jpg
                    other_image_count = alarm["other_image_count"]
                    imageUrl = g_config.storageDir_www + image_path
                    imageUrlArray.append(imageUrl)  # 第一张封面图

                    if other_image_count > 0:
                        image_path_ss = image_path.split(".")
                        if len(image_path_ss) == 2:
                            image_path_l = image_path_ss[0]  # alarm/control823181fa71/20240810/094055/1/20240810094055
                            image_path_r = image_path_ss[1]  # jpg

                            for i in range(other_image_count):
                                __imageUrl = g_config.storageDir_www + "%s_%d.%s" % (image_path_l, (i + 1), image_path_r)
                                imageUrlArray.append(__imageUrl)

                info["imageUrlArray"] = imageUrlArray
                # 获取并拼接所有图片end

                g_database.execute("update eai_node_alarm set is_check=1 where id <= %d " % int(alarm["id"]))
                ret = True
                msg = "success"
            except Exception as e:
                msg = _("检测报警新数据失败") + ":" + str(e)
                g_logger.error(msg)
        else:
            msg = _("暂无新数据")
    else:
        msg = _("暂无新数据")

    res = {
        "code": 1000 if ret else 0,
        "msg": msg,
        "info": info
    }
    return f_responseJson(res)
