import django
from django.conf import settings

# 配置 Django 设置
if not settings.configured:
    settings.configure(
        SECRET_KEY='test-secret-key',
        PASSWORD_HASHERS=[
            'django.contrib.auth.hashers.PBKDF2PasswordHasher',
        ],
    )
    django.setup()

from django.contrib.auth.hashers import make_password

# 生成推荐密码
recommended = [
    ("admin123", "简单易记的管理员密码"),
    ("Admin@123", "包含大小写和特殊字符"),
    ("123456", "最简单的密码"),
]

print("🔐 推荐的新密码及其哈希值：\n")
print("=" * 100)

for pwd, desc in recommended:
    hashed = make_password(pwd)
    print(f"\n密码：{pwd}  ({desc})")
    print(f"哈希：{hashed}")
    print("-" * 100)

print("\n\n💡 使用方法：")
print("1. 选择一个密码，复制对应的哈希值")
print("2. 在 eai.sql 文件的第159行，将旧哈希值替换为新哈希值")
print("3. 重新导入数据库")

