from django.db import models
# from pgvector.django import VectorField

class AiInterfaceModel(models.Model):
    user_id = models.IntegerField(verbose_name='user_id')
    sort = models.IntegerField(verbose_name='sort')
    code = models.CharField(max_length=50, verbose_name='code')
    address = models.TextField(verbose_name='address')
    api_key = models.CharField(max_length=100, verbose_name='api_key')
    state = models.IntegerField(verbose_name='状态')  # 0:未处理 1:已处理（正常报警） 2:已处理（误报） 5:逻辑删除
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='create_time')
    last_update_time = models.DateTimeField(verbose_name='last_update_time')
    model_name = models.CharField(max_length=100, verbose_name='model_name')

    def __repr__(self):
        return self.code

    def __str__(self):
        return self.code

    class Meta:
        db_table = 'eai_ai_interface'
        verbose_name = 'eai_ai_interface'
        verbose_name_plural = 'eai_ai_interface'

class NodeModel(models.Model):
    # id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(verbose_name='user_id')
    sort = models.IntegerField(verbose_name='sort')
    code = models.CharField(max_length=50, verbose_name='code')
    nickname = models.CharField(max_length=100, verbose_name='昵称')
    version = models.FloatField(verbose_name='version')
    flag = models.CharField(max_length=50, verbose_name='flag')
    system_name = models.CharField(max_length=100, verbose_name='system_name')
    machine_node = models.CharField(max_length=100, verbose_name='machine_node')
    address = models.CharField(max_length=200, verbose_name='address')
    eai_safe = models.CharField(max_length=100, verbose_name='eai_safe')
    media_secret = models.CharField(max_length=100, verbose_name='media_secret')
    machine_mac = models.CharField(max_length=50, verbose_name='machine_mac')
    is_auth = models.IntegerField(verbose_name='is_auth')
    is_multi_process = models.IntegerField(verbose_name='is_multi_process')
    max_count = models.IntegerField(verbose_name='max_count')
    desc = models.CharField(max_length=200, verbose_name='desc')
    auth_info = models.TextField(verbose_name='auth_info')
    state = models.IntegerField(verbose_name='state')  # 默认0   0:未同步 1:在线 2:掉线 3:版本不支持 4:读取节点信息失败

    image_path = models.CharField(max_length=200, verbose_name='image_path')
    expand1 = models.CharField(max_length=200, verbose_name='expand1')
    expand2 = models.CharField(max_length=200, verbose_name='expand2')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='create_time')
    last_update_time = models.DateTimeField(auto_now_add=True, verbose_name='last_update_time')

    node_code = models.CharField(max_length=100, verbose_name='node_code')
    node_host = models.CharField(max_length=100, verbose_name='node_host')

    def __repr__(self):
        return self.code

    def __str__(self):
        return self.code

    class Meta:
        db_table = 'eai_node'
        verbose_name = 'eai_node'
        verbose_name_plural = 'eai_node'
class NodeAlarmModel(models.Model):
    sort = models.IntegerField(verbose_name='sort')
    code = models.CharField(max_length=50, verbose_name='code')
    event_id = models.CharField(max_length=64, default='', blank=True, verbose_name='边缘推送事件ID（幂等去重键）')
    draw_type = models.IntegerField(verbose_name='合成报警视频画框类型')  # 1:画框 0:未画框
    flag = models.CharField(max_length=50, verbose_name='合成报警视频标记')
    node_code = models.CharField(max_length=100, verbose_name='node_code')
    control_code = models.CharField(max_length=50, verbose_name='布控编号')
    desc = models.CharField(max_length=200, verbose_name='描述')
    video_path = models.TextField(verbose_name='视频存储路径')
    video_count = models.IntegerField(verbose_name='视频总数量')
    image_path = models.TextField(verbose_name='主图存储路径')
    image_count = models.IntegerField(verbose_name='图片总数量')
    other_image_count = models.IntegerField(verbose_name='其他图片数量')
    level = models.IntegerField(verbose_name='报警级别')  # 0:普通 1:警告 2:严重
    risk_level = models.IntegerField(default=0, verbose_name='风险等级')  # 0:低 1:中 2:高（边缘推送）
    state = models.IntegerField(verbose_name='状态')  # 0:未读 1:未处理 2:已处理 3:误报 5:逻辑删除
    is_check = models.IntegerField(verbose_name='是否检测')  # 0 未被检测到报警 1 已被页面检测到报警
    deal_info = models.CharField(max_length=500, default='', blank=True, verbose_name='处理信息')
    alarm_category = models.IntegerField(default=0, verbose_name='告警分类')  # 0:事件 1:车牌 2:人脸 3:计数
    review_remark = models.CharField(max_length=200, verbose_name='审核备注')
    stream_app = models.CharField(max_length=50, verbose_name='视频流应用')
    stream_name = models.CharField(max_length=100, verbose_name='视频流名称')
    stream_code = models.CharField(max_length=50, verbose_name='视频流编号')
    flow_mode = models.IntegerField(verbose_name='业务算法模式')
    flow_code = models.CharField(max_length=50, verbose_name='业务算法编号')
    flow_name = models.CharField(max_length=100, verbose_name='业务算法名称')
    task_name = models.CharField(max_length=200, default='', blank=True, verbose_name='算法任务名称（边缘推送）')
    detect_objs = models.TextField(default='', blank=True, verbose_name='检测对象(JSON数组)')
    # v4.610新增
    main_plate_color = models.IntegerField(verbose_name='关键帧车牌颜色')
    main_plate_type = models.IntegerField(verbose_name='关键帧车牌类型')
    main_plate_no = models.CharField(max_length=100, verbose_name='关键帧车牌号')
    main_track_max_code = models.CharField(max_length=50, verbose_name='特征最大匹配编号')
    main_track_max_custom_code = models.CharField(max_length=50, verbose_name='特征最大匹配自定义编号')
    main_track_max_similary = models.IntegerField(verbose_name='特征最大相似度')
    expand1 = models.CharField(max_length=200, verbose_name='expand1')
    expand2 = models.CharField(max_length=200, verbose_name='expand2')

    create_time = models.DateTimeField(auto_now_add=True, verbose_name='create_time')
    create_timestamp = models.IntegerField(verbose_name='create_timestamp')  # 秒级时间戳
    last_update_time = models.DateTimeField(verbose_name='last_update_time')

    def __repr__(self):
        return self.desc

    def __str__(self):
        return self.desc
    def delete(self, using=None, keep_parents=False):
        ret = super(NodeAlarmModel, self).delete(using, keep_parents)
        return ret
    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        ret = super(NodeAlarmModel, self).save(force_insert, force_update, using, update_fields)
        return ret

    class Meta:
        db_table = 'eai_node_alarm'
        verbose_name = 'eai_node_alarm'
        verbose_name_plural = 'eai_node_alarm'

class NodeMediaSourceModel(models.Model):
    node_code = models.CharField(max_length=100, verbose_name='节点编号(eai_node.code)')
    source_code = models.CharField(max_length=50, verbose_name='边缘媒体源编号(av_media_source.code)')
    source_type = models.IntegerField(default=1, verbose_name='源类型')  # 1:RTSP 2:RTMP 3:FILE 4:ONVIF 5:GB28181
    app = models.CharField(max_length=50, verbose_name='分组')
    name = models.CharField(max_length=50, verbose_name='名称')
    nickname = models.CharField(max_length=200, default='', blank=True, verbose_name='昵称')
    forward_state = models.IntegerField(default=0, verbose_name='转发状态')  # 0:未转发 1:转发中
    online_state = models.IntegerField(default=0, verbose_name='在线状态')  # 0:未知 1:在线 2:离线
    extra = models.TextField(default='', blank=True, verbose_name='源参数JSON')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='create_time')
    last_update_time = models.DateTimeField(verbose_name='last_update_time')

    def __repr__(self):
        return self.source_code

    def __str__(self):
        return self.source_code

    class Meta:
        db_table = 'eai_node_media_source'
        verbose_name = 'eai_node_media_source'
        verbose_name_plural = 'eai_node_media_source'

class NodeStatisticAlarmModel(models.Model):
    node_code = models.CharField(max_length=100, verbose_name='节点编号(eai_node.code)')
    control_code = models.CharField(max_length=50, verbose_name='布控编号')
    task_name = models.CharField(max_length=200, verbose_name='算法任务名称')
    count = models.IntegerField(default=0, verbose_name='当前数量')
    enter_num = models.IntegerField(default=0, verbose_name='进入数量')
    leave_num = models.IntegerField(default=0, verbose_name='离开数量')
    total_num = models.IntegerField(default=0, verbose_name='总数量')
    snap_url = models.CharField(max_length=500, default='', blank=True, verbose_name='快照URL')
    reset_strategy = models.CharField(max_length=20, default='manual', verbose_name='清零策略')
    last_reset_time = models.DateTimeField(null=True, blank=True, verbose_name='上次清零时间')
    update_time = models.DateTimeField(verbose_name='update_time')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='create_time')

    def __repr__(self):
        return self.task_name

    def __str__(self):
        return self.task_name

    class Meta:
        db_table = 'eai_node_statistic_alarm'
        verbose_name = 'eai_node_statistic_alarm'
        verbose_name_plural = 'eai_node_statistic_alarm'

class NodeStatisticHistoryModel(models.Model):
    """计数历史：每个清零周期归档一条汇总（边缘 statistic_reset / 云端手动清零时归档）。"""
    node_code = models.CharField(max_length=100, verbose_name='节点编号(eai_node.code)')
    control_code = models.CharField(max_length=50, verbose_name='布控编号')
    task_name = models.CharField(max_length=200, verbose_name='算法任务名称')
    enter_num = models.IntegerField(default=0, verbose_name='进入数量')
    leave_num = models.IntegerField(default=0, verbose_name='离开数量')
    total_num = models.IntegerField(default=0, verbose_name='总数量')
    snap_url = models.CharField(max_length=500, default='', blank=True, verbose_name='快照URL')
    reset_strategy = models.CharField(max_length=20, default='manual', verbose_name='清零策略')
    period_start = models.DateTimeField(null=True, blank=True, verbose_name='周期开始(上次清零时间)')
    period_end = models.DateTimeField(verbose_name='周期结束(归档时间)')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='create_time')

    def __repr__(self):
        return "%s/%s" % (self.control_code, self.task_name)

    def __str__(self):
        return "%s/%s" % (self.control_code, self.task_name)

    class Meta:
        db_table = 'eai_node_statistic_history'
        verbose_name = 'eai_node_statistic_history'
        verbose_name_plural = 'eai_node_statistic_history'

class NodeStreamModel(models.Model):
    sort = models.IntegerField(verbose_name='排序')
    stream_code = models.CharField(max_length=50, verbose_name='stream_code')
    stream_nickname = models.CharField(max_length=100, verbose_name='stream_nickname')
    node_codes = models.TextField(verbose_name='节点编号列表')
    state = models.IntegerField(verbose_name='状态')  # 0:默认状态 该参数暂未使用
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='create_time')
    last_update_time = models.DateTimeField(verbose_name='last_update_time')
    def __repr__(self):
        return self.stream_code

    def __str__(self):
        return self.stream_code

    class Meta:
        db_table = 'eai_node_stream'
        verbose_name = 'eai_node_stream'
        verbose_name_plural = 'eai_node_stream'

class NodeAlgorithmFlowModel(models.Model):
    sort = models.IntegerField(verbose_name='排序')
    flow_code = models.CharField(max_length=50, verbose_name='flow_code')
    flow_name = models.CharField(max_length=100, verbose_name='flow_name')
    node_codes = models.TextField(verbose_name='节点编号列表')
    state = models.IntegerField(verbose_name='状态')  # 0:默认状态 该参数暂未使用
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='create_time')
    last_update_time = models.DateTimeField(verbose_name='last_update_time')
    def __repr__(self):
        return self.flow_code

    def __str__(self):
        return self.flow_code

    class Meta:
        db_table = 'eai_node_algorithm_flow'
        verbose_name = 'eai_node_algorithm_flow'
        verbose_name_plural = 'eai_node_algorithm_flow'

