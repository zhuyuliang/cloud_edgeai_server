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

password_to_test = "22"
stored_hash = "pbkdf2_sha256$720000$HlUv1lYeLRdrPs6pbW1sFV$j4TJk/syazz989sFPZwIHg8vTMLGY5KZmVOSYlCucO4="

if check_password(password_to_test, stored_hash):
    print("✅ 密码匹配！原始密码是: 22")
else:
    print("❌ 密码不匹配")