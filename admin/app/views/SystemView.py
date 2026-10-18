import json
import shutil
import time
from app.views.ViewsBase import *
from django.shortcuts import render, redirect
import os
import threading
from app.utils.TarUtils import TarUtils
from app.utils.UploadUtils import UploadUtils
from app.utils.OSSystem import OSSystem
from framework.settings import PROJECT_VERSION,PROJECT_ADMIN_START_TIMESTAMP
from django.utils.translation import gettext as _

def settings(request):
    # 系统设置
    # 读取settings.json获取系统基本信息
    system_settings = f_settingsReadData()
    
    # 读取config.json获取配置信息
    import json
    config_data = {}
    try:
        with open(g_filepath_config_json, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except Exception as e:
        g_logger.error(f"SystemView.settings() error reading config.json: {str(e)}")
    
    context = {
        "settings": system_settings,  # 用于模板中的系统基本信息（如logo_url）
        "config": config_data,  # 用于配置编辑表单
        "project_version": PROJECT_VERSION,
        "project_flag": PROJECT_FLAG
    }
    return render(request, 'app/system/settings.html', context)

def api_postExportLogs(request):
    # 导出日志
    ret = False
    msg = _("未知错误")
    info = {

    }
    export_dir = None
    if request.method == 'POST':
        # 导出外层文件夹
        export_dirname = "logs%s-%s-%s" % (PROJECT_VERSION, PROJECT_FLAG, datetime.now().strftime("%Y%m%d%H%M%S"))
        export_dir = os.path.join(g_config.storageTempDir, export_dirname)
        export_tar_filepath = os.path.join(g_config.storageTempDir, "%s.tar" % export_dirname)  # export_dir压缩后的tar文件
        export_filename = "%s.xclogs" % export_dirname
        export_filepath = os.path.join(g_config.storageTempDir, export_filename)

        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        # 压缩工具
        tar_utils = TarUtils()
        osSystem = OSSystem()


        # 压缩log->log.tar
        log_dir = "log"
        if os.path.exists(log_dir):
            log_tar_filepath = os.path.join(export_dir, "log.tar")
            tar_utils.compress_folder(folder_dir=log_dir, output_filepath=log_tar_filepath)

        # （v4.632新增）写入config.json, settings.json, config.ini
        if os.path.exists(g_filepath_config_json):
            dst = os.path.join(export_dir, "config.json")
            shutil.copyfile(g_filepath_config_json, dst)

        if os.path.exists(g_filepath_settings_json):
            dst = os.path.join(export_dir, "settings.json")
            shutil.copyfile(g_filepath_settings_json, dst)

        # v4.701新增 end

        # （v4.632新增）写入环境信息
        export_filepath_env = os.path.join(export_dir, "env.txt")
        env_f = open(export_filepath_env, 'w', encoding="utf-8")
        env_f.write("name=%s\n" % PROJECT_UA)
        env_f.write("built=%s\n" % PROJECT_BUILT)
        env_f.write("version=%s\n" % PROJECT_VERSION)
        env_f.write("flag=%s\n" % PROJECT_FLAG)
        env_f.write("log_filename=%s\n" % export_filename)
        env_f.write("app_start_date=%s\n" % datetime.fromtimestamp(PROJECT_ADMIN_START_TIMESTAMP).strftime('%Y-%m-%d %H:%M'))
        env_f.write("current_date=%s\n" % datetime.now().strftime('%Y-%m-%d %H:%M'))
        env_f.write("system=%s\n" % osSystem.getSystemName())
        env_f.write("machine=%s\n" % osSystem.getMachineNode())
        env_f.write("os=%s\n" % str(osSystem.getOSInfo()))
        env_f.write("os_release=%s\n" % osSystem.getMachineOsRelease())
        env_f.write("eai_log=%s\n" % str(g_database.select("select * from eai_log order by id desc")))
        env_f.write("cpu=%s\n" % osSystem.getMachineCpu())
        env_f.write("nvidia=%s\n" % osSystem.getMachineNvidia())
        env_f.write("ascend=%s\n" % osSystem.getMachineAscend())
        env_f.write("rknpu=%s\n" % osSystem.getMachineRknpu())
        env_f.close()

        # 导出文件夹的压缩
        tar_utils.compress_folder(folder_dir=export_dir, output_filepath=export_tar_filepath)
        shutil.move(export_tar_filepath, export_filepath) # 文件改名
        export_tar_filepath = None

        info["export_filename"] = export_filename
        ret = True
        msg = _("导出日志成功")

    else:
        msg = "request method not supported"

    g_logger.info("SystemView.postExportLogs() export_dir=%s" % str(export_dir))
    if export_dir:
        try:
            if os.path.exists(export_dir):
                shutil.rmtree(export_dir)
        except Exception as e:
            g_logger.error("e=%s" % str(e))

    res = {
        "code": 1000 if ret else 0,
        "msg": msg,
        "info": info
    }
    g_logger.info("SystemView.postExportLogs() res:%s" % str(res))
    return f_responseJson(res)

def api_postSaveSettings(request):
    # 保存系统配置
    ret = False
    msg = _("未知错误")
    info = {}
    
    if request.method == 'POST':
        try:
            # 读取现有配置
            with open(g_filepath_config_json, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 更新配置
            for key, value in request.POST.items():
                # 处理布尔值
                if value.lower() == 'true':
                    config_data[key] = True
                elif value.lower() == 'false':
                    config_data[key] = False
                # 处理数字
                elif value.isdigit():
                    config_data[key] = int(value)
                # 处理字符串
                else:
                    config_data[key] = value
            
            # 保存配置
            with open(g_filepath_config_json, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            
            ret = True
            msg = _("保存配置成功")
        except Exception as e:
            msg = _("保存失败") + f"：{str(e)}"
            g_logger.error(f"SystemView.api_postSaveSettings() error: {str(e)}")
    else:
        msg = "request method not supported"
    
    res = {
        "code": 1000 if ret else 0,
        "msg": msg,
        "info": info
    }
    g_logger.info(f"SystemView.api_postSaveSettings() res: {str(res)}")
    return f_responseJson(res)
