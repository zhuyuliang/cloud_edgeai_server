-- =====================================================================
-- 云端集群管理平台 存量库升级脚本（配套 云端告警布控逻辑对齐方案-V2.md）
-- 适用：已部署的 eai_admin MySQL 库（新部署直接使用 docker/database.sql）
-- 执行前请先备份！
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. eai_node_alarm 结构升级 + 状态语义迁移
--    新语义: 0:未读 1:未处理 2:已处理 3:误报 5:逻辑删除(不变)
--    注意：UPDATE 必须降序执行（3→2→1→0 逆序），避免连锁覆盖！
-- ---------------------------------------------------------------------

-- 1.1 新增字段
ALTER TABLE `eai_node_alarm`
  ADD COLUMN `event_id` varchar(64) NOT NULL DEFAULT '' COMMENT '边缘推送事件ID（幂等去重键）' AFTER `code`,
  ADD COLUMN `risk_level` smallint NOT NULL DEFAULT 0 COMMENT '风险等级 0低1中2高（边缘推送）' AFTER `level`,
  ADD COLUMN `deal_info` varchar(500) NOT NULL DEFAULT '' COMMENT '处理信息' AFTER `is_check`,
  ADD COLUMN `alarm_category` smallint NOT NULL DEFAULT 0 COMMENT '0:事件 1:车牌 2:人脸 3:计数' AFTER `deal_info`,
  ADD COLUMN `task_name` varchar(200) NOT NULL DEFAULT '' COMMENT '算法任务名称（边缘推送）' AFTER `flow_name`,
  ADD COLUMN `detect_objs` text NULL COMMENT '检测对象(JSON数组)' AFTER `task_name`;

-- 1.2 存量状态迁移（降序！2→3 先执行）
UPDATE `eai_node_alarm` SET `state` = 3 WHERE `state` = 2;   -- 旧"误报"   → 新"误报"
UPDATE `eai_node_alarm` SET `state` = 2 WHERE `state` = 1;   -- 旧"已处理" → 新"已处理"
UPDATE `eai_node_alarm` SET `state` = 1 WHERE `state` = 0;   -- 旧"未处理" → 新"未处理"
-- state=5 逻辑删除保持不变

-- 1.3 event_id 唯一索引（存量行 event_id=''，MySQL 允许 '' 重复，新推送按前缀区分）
ALTER TABLE `eai_node_alarm` ADD UNIQUE INDEX `uk_event_id`(`event_id`);
ALTER TABLE `eai_node_alarm` ADD INDEX `idx_node_category_time`(`node_code`, `alarm_category`, `create_timestamp`);

-- ---------------------------------------------------------------------
-- 2. 新建 媒体源同步表
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `eai_node_media_source`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `node_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点编号(eai_node.code)',
  `source_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '边缘媒体源编号(av_media_source.code)',
  `source_type` smallint NOT NULL DEFAULT 1 COMMENT '源类型 1:RTSP 2:RTMP 3:FILE 4:ONVIF 5:GB28181',
  `app` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `nickname` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '',
  `forward_state` smallint NOT NULL DEFAULT 0 COMMENT '0:未转发 1:转发中',
  `online_state` smallint NOT NULL DEFAULT 0 COMMENT '0:未知 1:在线 2:离线',
  `extra` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '源参数JSON(拉流地址/设备信息/GB参数等,敏感字段脱敏)',
  `create_time` datetime NOT NULL,
  `last_update_time` datetime NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_node_source`(`node_code` ASC, `source_code` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '节点媒体源同步表' ROW_FORMAT = Dynamic;

-- ---------------------------------------------------------------------
-- 3. 新建 统计告警表
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `eai_node_statistic_alarm`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `node_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点编号(eai_node.code)',
  `control_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '布控编号',
  `task_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '算法任务名称',
  `count` int NOT NULL DEFAULT 0 COMMENT '当前数量',
  `enter_num` int NOT NULL DEFAULT 0 COMMENT '进入数量',
  `leave_num` int NOT NULL DEFAULT 0 COMMENT '离开数量',
  `total_num` int NOT NULL DEFAULT 0 COMMENT '总数量',
  `snap_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '快照URL',
  `reset_strategy` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'manual' COMMENT '清零策略 manual/daily/weekly/monthly',
  `last_reset_time` datetime NULL DEFAULT NULL COMMENT '上次清零时间',
  `update_time` datetime NOT NULL,
  `create_time` datetime NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_node_control_task`(`node_code` ASC, `control_code` ASC, `task_name` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '节点统计告警表' ROW_FORMAT = Dynamic;

-- ---------------------------------------------------------------------
-- 4. 新建 计数历史表（每个清零周期归档一条汇总）
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `eai_node_statistic_history`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `node_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '节点编号(eai_node.code)',
  `control_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '布控编号',
  `task_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '算法任务名称',
  `enter_num` int NOT NULL DEFAULT 0 COMMENT '进入数量',
  `leave_num` int NOT NULL DEFAULT 0 COMMENT '离开数量',
  `total_num` int NOT NULL DEFAULT 0 COMMENT '总数量',
  `snap_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '快照URL',
  `reset_strategy` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'manual' COMMENT '清零策略 manual/hourly/daily/weekly/monthly',
  `period_start` datetime NULL DEFAULT NULL COMMENT '周期开始(上次清零时间)',
  `period_end` datetime NOT NULL COMMENT '周期结束(归档时间)',
  `create_time` datetime NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_node_control_task`(`node_code` ASC, `control_code` ASC, `task_name` ASC, `period_end` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '节点计数历史表(周期归档)' ROW_FORMAT = Dynamic;
