#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 数据库连接测试脚本
用于测试 Docker MySQL 容器的连接情况
"""

import pymysql
import sys
from pymysql.cursors import DictCursor


def test_connection():
    """测试数据库连接"""
    print("=" * 50)
    print("开始测试 MySQL 数据库连接...")
    print("=" * 50)
    
    connection = None
    try:
        # 创建数据库连接
        print("\n[1] 正在连接数据库...")
        connection = pymysql.connect(
            host='127.0.0.1',
            port=5456,
            user='root',
            password='你的数据库密码',
            database='eaihub',
            charset='utf8mb4',
            cursorclass=DictCursor
        )
        print("✓ 数据库连接成功！")
        
        # 获取数据库版本
        print("\n[2] 正在获取数据库版本...")
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION() as version")
            result = cursor.fetchone()
            print(f"✓ MySQL 版本: {result['version']}")
        
        # 获取当前数据库
        print("\n[3] 正在获取当前数据库...")
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE() as db_name")
            result = cursor.fetchone()
            print(f"✓ 当前数据库: {result['db_name']}")
        
        # 列出所有表
        print("\n[4] 正在列出数据库中的表...")
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            if tables:
                print(f"✓ 找到 {len(tables)} 个表:")
                for table in tables:
                    table_name = list(table.values())[0]
                    print(f"  - {table_name}")
            else:
                print("  ℹ 数据库中暂无表")
        
        # 测试写入权限
        print("\n[5] 正在测试写入权限...")
        with connection.cursor() as cursor:
            # 创建测试表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_connection (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    test_time DATETIME,
                    message VARCHAR(255)
                )
            """)
            print("✓ 创建测试表成功")
            
            # 插入测试数据
            cursor.execute("""
                INSERT INTO test_connection (test_time, message)
                VALUES (NOW(), '连接测试成功')
            """)
            connection.commit()
            print("✓ 插入测试数据成功")
            
            # 查询测试数据
            cursor.execute("SELECT * FROM test_connection ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            print(f"✓ 读取测试数据成功: {result}")
            
            # 删除测试表
            cursor.execute("DROP TABLE IF EXISTS test_connection")
            connection.commit()
            print("✓ 清理测试表成功")
        
        print("\n" + "=" * 50)
        print("✓ 所有测试通过！数据库连接正常")
        print("=" * 50)
        return True
        
    except pymysql.err.OperationalError as e:
        print(f"\n✗ 连接错误: {e}")
        print("\n可能的原因:")
        print("  1. MySQL 容器未启动")
        print("  2. 端口映射不正确")
        print("  3. 用户名或密码错误")
        print("\n建议:")
        print("  - 运行: bash start-mysql.sh")
        print("  - 检查: docker ps | grep mysql")
        return False
        
    except pymysql.err.ProgrammingError as e:
        print(f"\n✗ 数据库错误: {e}")
        print("\n可能的原因:")
        print("  1. 数据库不存在")
        print("  2. SQL 语句错误")
        return False
        
    except Exception as e:
        print(f"\n✗ 未知错误: {e}")
        print(f"错误类型: {type(e).__name__}")
        return False
        
    finally:
        if connection:
            connection.close()
            print("\n[6] 数据库连接已关闭")


def check_pymysql():
    """检查 pymysql 模块是否已安装"""
    try:
        import pymysql
        print(f"✓ pymysql 已安装 (版本: {pymysql.__version__})")
        return True
    except ImportError:
        print("✗ pymysql 未安装")
        print("\n请运行以下命令安装:")
        print("  pip install pymysql")
        return False


if __name__ == "__main__":
    print("\n检查依赖...")
    if not check_pymysql():
        sys.exit(1)
    
    print()
    success = test_connection()
    
    if not success:
        sys.exit(1)
