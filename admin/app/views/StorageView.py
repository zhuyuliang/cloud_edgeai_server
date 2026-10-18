from app.views.ViewsBase import *
from app.utils.Utils import get_folder_size
from django.utils.encoding import escape_uri_path
from django.utils.translation import gettext as _
import os

def info(request):
    ret = False
    msg = _("未知错误")
    info = {}
    t1 = time.time()
    if request.method == 'GET':
        __check_ret, __check_msg = f_checkRequestSafe(request)
        if __check_ret:
            try:
                alarm_folder_size_GB = get_folder_size(g_config.storageAlarmDir)
                record_folder_size_GB = get_folder_size(g_config.storageRecordDir)

                info = {
                    "storageDir": g_config.storageDir,
                    "storageDir_www": "http://" + g_config.externalHost + ":" + str(g_config.adminPort) + g_config.storageDir_www,
                    "storageAlarmMaxSize": g_config.storageAlarmMaxSize,
                    "storageRecordMaxSize": g_config.storageRecordMaxSize,
                    "alarmFolderSize": round(alarm_folder_size_GB,2),
                    "recordFolderSize": round(record_folder_size_GB,2)
                }
                ret = True
                msg = "success"
            except Exception as e:
                 msg = str(e)
        else:
            msg = __check_msg
    else:
        msg = "request method not supported"

    t2 = time.time()
    duration = round(t2 - t1, 3)

    res = {
        "code": 1000 if ret else 0,
        "msg": msg,
        "info": info,
        "duration": duration
    }
    g_logger.info("StorageView.info() res:%s" % str(res))

    return f_responseJson(res)

def download(request):
    params = f_parseGetParams(request)
    g_logger.info("StorageView.download() params:%s" % str(params))

    filename = params.get("filename")
    try:
        if filename:
            if filename.endswith(".mp4") \
                    or filename.endswith(".avi") \
                    or filename.endswith(".wav") \
                    or filename.endswith(".jpg") \
                    or filename.endswith(".jpeg") \
                    or filename.endswith(".png") \
                    or filename.endswith(".tar") \
                    or filename.endswith(".xclogs") \
                    or filename.endswith(".xcsettings") \
                    or filename.endswith(".xcflow"):

                filepath = os.path.join(g_config.storageTempDir, filename)

                if os.path.exists(filepath):
                    f = open(filepath, mode="rb")
                    data = f.read()
                    f.close()
                    response = HttpResponse(data, content_type="application/octet-stream")
                    response['Access-Control-Allow-Origin'] = "*"
                    response['Access-Control-Allow-Headers'] = "*"
                    response['Access-Control-Allow-Methods'] = "POST, GET, OPTIONS, DELETE"
                    response['Content-Disposition'] = "attachment;filename={};".format(escape_uri_path(filename))
                    try:
                        os.remove(filepath)
                    except Exception as e:
                        g_logger.error("storage/download completed, but delete error,filepath=%s : %s" % (filepath, str(e)))
                    return response
                else:
                    raise Exception("storage/download filepath not found")
            else:
                raise Exception("storage/download unsupported filename format")
        else:
            raise Exception("storage/download filename not found")

    except Exception as e:
        return f_responseJson({"msg": str(e)})

def access(request):
    params = f_parseGetParams(request)
    filename = params.get("filename")
    try:
        if filename:
            if (filename.endswith(".mp4") or
                    filename.endswith(".avi") or
                    filename.endswith(".wav") or
                    filename.endswith(".jpeg") or
                    filename.endswith(".jpg") or
                    filename.endswith(".png") or
                    filename.endswith(".csv")):

                filepath = os.path.join(g_config.storageDir, filename)

                if os.path.exists(filepath):
                    f = open(filepath, mode="rb")
                    data = f.read()
                    f.close()

                    if filename.endswith(".mp4"):
                        fs = os.path.getsize(filepath)
                        response = HttpResponse(data, content_type="video/mp4")
                        response['Accept-Ranges'] = "bytes"
                        response['Access-Control-Allow-Origin'] = "*"
                        response['Access-Control-Allow-Headers'] = "*"
                        response['Access-Control-Allow-Methods'] = "POST, GET, OPTIONS, DELETE"
                        response['Content-Length'] = fs
                        # response['Content-Range'] = "bytes 32768-188720863/188720864"
                        # response['Etag'] = "66dc3116-b3fa6e0"
                        # response['Content-Disposition'] = "attachment;filename={};".format(escape_uri_path(filename))
                    elif filename.endswith(".csv"):
                        # 导出文件以附件形式下载
                        response = HttpResponse(data, content_type="text/csv")
                        response['Access-Control-Allow-Origin'] = '*'
                        response['Content-Disposition'] = "attachment;filename={};".format(escape_uri_path(os.path.basename(filename)))
                    elif filename.endswith(".jpg") or filename.endswith(".png"):
                        response = HttpResponse(data, content_type="image/jpeg")
                        response['Access-Control-Allow-Origin'] = "*"
                        response['Access-Control-Allow-Headers'] = "*"
                        response['Access-Control-Allow-Methods'] = "POST, GET, OPTIONS, DELETE"
                    else:
                        response = HttpResponse(data, content_type="application/octet-stream")
                        response['Access-Control-Allow-Origin'] = "*"
                        response['Access-Control-Allow-Headers'] = "*"
                        response['Access-Control-Allow-Methods'] = "POST, GET, OPTIONS, DELETE"
                        response['Content-Disposition'] = "attachment;filename={};".format(escape_uri_path(filename))

                    return response
                else:
                    raise Exception("storage/access filepath not found")
            else:
                raise Exception("storage/access unsupported filename format")
        else:
            raise Exception("storage/access filename not exist")

    except Exception as e:
        return f_responseJson({"msg": str(e)})