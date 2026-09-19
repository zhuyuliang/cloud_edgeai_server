from django.urls import path
from .views import UserView
from .views import IndexView
from .views import NodeView
from .views import AlarmView
from .views import StreamView
from .views import ControlView
from .views import OpenView
from .views import StorageView
from .views import SystemView
from .views import VersionView
from .views import InnerlView

app_name = 'app'

urlpatterns = [
    # 主页功能
    path('', IndexView.index),
    path('dashboard', IndexView.dashboard),
    path('index/updateDashboardData', IndexView.api_updateDashboardData),
    path('index/getDashboardData', IndexView.api_getDashboardData),
    path('index/getDashboardPlayerData', IndexView.api_getDashboardPlayerData),
    path('index/getNewAlarm', IndexView.api_getNewAlarm),

    # 登陆退出
    path('captcha', UserView.captcha),
    path('login', UserView.login),
    path('logout', UserView.logout),

    # 用户管理
    path('user/index', UserView.index),
    path('user/add', UserView.add),
    path('user/edit', UserView.edit),
    path('user/postDel', UserView.api_postDel),
    path('user/api_openUserDetail', UserView.api_openUserDetail),


    # 节点管理
    path('node/index', NodeView.index),
    path('node/add', NodeView.add),
    path('node/edit', NodeView.edit),
    path('node/openDel', NodeView.api_openDel),
    path('node/openSync', NodeView.api_openSync),
    path('node/openImportUpdate', NodeView.api_openImportUpdate),
    path('node/openNodeDetail', NodeView.api_openNodeDetail),
    # 报警管理
    path('alarm/event', AlarmView.page_event),
    path('alarm/carplate', AlarmView.page_carplate),
    path('alarm/face', AlarmView.page_face),
    path('alarm/count', AlarmView.page_count),
    path('alarm/count/history', AlarmView.page_countHistory),
    path('alarm/openHandle', AlarmView.api_openHandle),
    path('alarm/openExport', AlarmView.api_openExport),
    path('alarm/openIndex', AlarmView.api_openIndex),
    path('alarm/openInfo', AlarmView.api_openInfo),
    path('alarm/openPush', AlarmView.api_openPush),
    path('alarm/openUploadFile', AlarmView.api_openUploadFile),
    path('alarm/openStatisticIndex', AlarmView.api_openStatisticIndex),
    path('alarm/openStatisticHistory', AlarmView.api_openStatisticHistory),
    path('alarm/openDeleteStatisticHistory', AlarmView.api_openDeleteStatisticHistory),
    path('alarm/openExportStatisticHistory', AlarmView.api_openExportStatisticHistory),
    path('alarm/openResetCount', AlarmView.api_openResetCount),

    # 节点视频管理
    path('stream/index', StreamView.index),
    path('stream/openIndex', StreamView.api_openIndex),
    path('stream/openAddStreamProxy', StreamView.api_openAddStreamProxy),
    path('stream/openDelStreamProxy', StreamView.api_openDelStreamProxy),
    path('stream/openHandleAllStreamProxy', StreamView.api_openHandleAllStreamProxy),
    path('stream/openDel', StreamView.api_openDel),
    path('stream/player', StreamView.player),
    # 节点页面代理（iframe 双跳：云端登录态 + 边缘 Eai-Secret）
    path('proxy/node/<node_code>/<path:path>', StreamView.proxy_node),

    # 节点布控管理
    path('control/index', ControlView.index),
    path('control/openIndex', ControlView.api_openIndex),
    path('control/add', ControlView.add),
    path('control/openAdd', ControlView.api_openAdd),
    path('control/edit', ControlView.edit),
    path('control/openEdit', ControlView.api_openEdit),
    path('control/openLog', ControlView.api_openLog),
    path('control/openDel', ControlView.api_openDel),
    path('control/openCopy', ControlView.api_openCopy),
    path('control/openSettings', ControlView.api_openSettings),
    path('control/openHandleAllControl', ControlView.api_openHandleAllControl),
    path('control/openStartControl', ControlView.api_openStartControl),
    path('control/openStopControl', ControlView.api_openStopControl),


    # 内部接口
    path('inner/on_stream_not_found', InnerlView.api_on_stream_not_found),


    # 开放接口
    path('open/getIndex', OpenView.api_getIndex),
    path('open/getZlmProcessData', OpenView.api_getZlmProcessData),
    path('open/getAllCoreProcessData', OpenView.api_getAllCoreProcessData),
    path('open/getAllCoreProcessData2', OpenView.api_getAllCoreProcessData2),
    path('open/getAllStreamData', OpenView.api_getAllStreamData),
    path('open/getControl', OpenView.api_getControl),
    path('open/restartApp', OpenView.api_restartApp),
    path('open/restartOS', OpenView.api_restartOS),


    # 下载模块
    path('storage/download', StorageView.download),
    path('storage/access', StorageView.access),
    path('storage/info', StorageView.info),


    # 系统功能
    path('system/config', SystemView.settings),
    path('system/postExportLogs', SystemView.api_postExportLogs),
    path('system/postSaveSettings', SystemView.api_postSaveSettings),


    # 版本功能
    path('version/index', VersionView.index),
    path('version/getCheckVersion', VersionView.api_getCheckVersion),

]
