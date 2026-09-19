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

# 生成一些建议的密码
passwords = {
    "admin123": None,
    "password123": None,
    "Admin@2024": None,
}

print("🔐 生成新密码哈希值：\n")

for pwd in passwords:
    hashed = make_password(pwd)
    print(f"密码: {pwd}")
    print(f"哈希值: {hashed}")
    print("-" * 80)
    print()

# 自定义密码
print("\n📝 如果您想使用自定义密码，请输入（或按回车跳过）：")
custom_pwd = input().strip()
if custom_pwd:
    custom_hash = make_password(custom_pwd)
    print(f"\n您的密码: {custom_pwd}")
    print(f"哈希值: {custom_hash}")
    print("\n将此哈希值替换到 SQL 文件中的第159行即可。")

