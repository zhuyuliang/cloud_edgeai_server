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

from django.contrib.auth.hashers import check_password

stored_hash = "pbkdf2_sha256$720000$HlUv1lYeLRdrPs6pbW1sFV$j4TJk/syazz989sFPZwIHg8vTMLGY5KZmVOSYlCucO4="

# 常见密码列表
common_passwords = [
    "admin", "admin123", "password", "123456", "12345678", 
    "password123", "admin@123", "root", "123456789",
    "22", "2022", "2023", "2024", "2025",
    "qwerty", "abc123", "111111", "000000",
    "Admin123", "Admin@123", "Admin", "test", "test123",
]

print("🔍 正在测试常见密码...\n")

for password in common_passwords:
    if check_password(password, stored_hash):
        print(f"✅ 找到了！原始密码是: {password}")
        break
    else:
        print(f"❌ {password}")
else:
    print("\n⚠️ 未找到匹配的密码")
    print("\n如果您需要访问系统，建议：")
    print("1. 直接在数据库中更新为新密码的哈希值")
    print("2. 使用 Django 管理命令重置密码")

