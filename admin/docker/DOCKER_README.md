# MySQL Docker 部署说明

## 配置信息

MySQL 配置已根据 `.db.json` 文件设置：

- **数据库名称**: eaihub
- **Root 密码**: 你的数据库密码
- **端口**: 5456
- **字符集**: utf8mb4

## 快速启动

### 方式一：使用启动脚本（推荐）

```bash
# 添加执行权限
chmod +x start-mysql.sh

# 启动 MySQL
./start-mysql.sh
```

### 方式二：使用 docker-compose

```bash
# 启动容器
docker-compose -p eaihub up -d

# 查看日志
docker-compose -p eaihub logs -f mysql

# 停止容器
docker-compose -p eaihub down

# 停止并删除数据卷
docker-compose -p eaihub down -v
```

### 方式三：使用 Docker 命令

```bash
docker run -d \
  --name eaihub_mysql \
  -e MYSQL_ROOT_PASSWORD=你的数据库密码 \
  -e MYSQL_DATABASE=eaihub \
  -p 5456:3306 \
  mysql:8.0
```

## 连接 MySQL

### 从容器内连接

```bash
docker exec -it eaihub_mysql mysql -uroot -p你的数据库密码 eaihub
```

### 从主机连接

```bash
mysql -h 127.0.0.1 -P 5456 -uroot -p你的数据库密码 eaihub
```

### Python 连接示例

```python
import pymysql

connection = pymysql.connect(
    host='127.0.0.1',
    port=5456,
    user='root',
    password='你的数据库密码',
    database='eaihub',
    charset='utf8mb4'
)
```

## 数据持久化

数据卷 `mysql_data` 会自动创建并挂载到 `/var/lib/mysql`，确保数据在容器重启后不会丢失。

查看数据卷：
```bash
docker volume ls | grep mysql_data
```

## 导入 SQL 文件

如果需要在容器启动时自动导入 SQL 文件：

1. 创建 `mysql-init` 目录
2. 将 SQL 文件放入该目录
3. 重新启动容器

```bash
mkdir -p mysql-init
cp ../eaihub.sql mysql-init/
docker-compose -p eaihub down
docker-compose -p eaihub up -d
```

## 常用命令

```bash
# 查看容器状态
docker ps | grep eaihub_mysql

# 进入容器
docker exec -it eaihub_mysql bash

# 查看日志
docker logs eaihub_mysql

# 重启容器
docker-compose -p eaihub restart mysql

# 备份数据库
docker exec eaihub_mysql mysqldump -uroot -p你的数据库密码 eaihub > backup.sql

# 恢复数据库
docker exec -i eaihub_mysql mysql -uroot -p你的数据库密码 eaihub < backup.sql
```

## 故障排查

### 端口已被占用

如果 5456 端口已被占用，修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "5457:3306"  # 改为 5457 或其他可用端口
```

### 容器启动失败

查看详细日志：
```bash
docker-compose -p eaihub logs mysql
```

### 权限问题

确保数据卷有正确的权限：
```bash
docker-compose -p eaihub down -v
docker-compose up -d
```

## 注意事项

- 生产环境请修改默认密码
- 建议定期备份数据库
- 注意防火墙规则配置
- 数据卷删除后数据将永久丢失

