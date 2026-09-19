import time
from app.views.ViewsBase import *
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from app.utils.OSSystem import OSSystem
from io import BytesIO
from app.utils.Utils import xc_decrypt,buildPageLabels
# （v4.644新增）生成验证码start
import random
import platform
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def random_color(min_val=50, max_val=200):
    """生成随机RGB颜色"""
    return (
        random.randint(min_val, max_val),
        random.randint(min_val, max_val),
        random.randint(min_val, max_val)
    )
def load_captcha_font(height):
    """跨平台字体加载（优先Linux兼容字体）"""
    osSystem = OSSystem()
    if osSystem.getSystemName() == "Windows":
        font_paths = [
            g_config.fontPath,  # 项目内嵌字体
            "C:\\Windows\\Fonts\\arial.ttf",  # Windows
            "C:\\Windows\\Fonts\\arialbd.ttf"  # Windows Bold
        ]
    else:
        font_paths = [
            g_config.fontPath,  # 项目内嵌字体
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux Bold
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"  # 备用字体
        ]
    
    # 使用更大的字体尺寸比例
    font_size = int(height * 0.75)  # 进一步增大字体比例，使字符更大
    
    for font_path in font_paths:
        try:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
                g_logger.info("load_captcha_font() success, font_path=%s, font_size=%d" % (font_path, font_size))
                return font, font_size
        except Exception as e:
            g_logger.error("load_captcha_font() error, font_path=%s, e=%s" % (font_path, str(e)))

    # 保底方案：尝试使用新版API或抛出错误
    g_logger.error("load_captcha_font() failed: no suitable font found")
    font_size = int(height * 0.75)
    try:
        # Pillow 10.0.0+ 支持 size 参数
        return ImageFont.load_default(size=font_size), font_size
    except TypeError:
        # 旧版本 Pillow 不支持 size 参数，返回固定大小字体（非常小）
        g_logger.warning("load_captcha_font() using old default font (very small)")
        return ImageFont.load_default(), font_size
    
def generate_secure_captcha(length=4):
    """生成带干扰线的验证码图片"""

    width = 240  # 增加宽度以容纳更大的字符
    height = 80  # 显著增加高度使字符更大更清晰
    font, font_size = load_captcha_font(height)

    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    # 生成随机文本（排除易混淆字符）
    chars = 'ABCDEFGHJKMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789'
    captcha_text = ''.join(random.choices(chars, k=length))

    # 计算每个字符的平均宽度空间
    char_width = (width - 40) // length  # 总宽度减去左右边距
    
    # 绘制字符
    x_offset = 20  # 左边距
    for i, char in enumerate(captcha_text):
        # 创建足够大的临时画布用于旋转字符
        temp_size = font_size * 3
        char_img = Image.new('RGBA', (temp_size, temp_size), (0, 0, 0, 0))
        char_draw = ImageDraw.Draw(char_img)
        
        # 将字符绘制在临时画布中心
        char_draw.text((temp_size // 2 - font_size // 2, temp_size // 2 - font_size // 2), 
                      char, font=font, fill=random_color(20, 80))
        # 方法1：使用 anchor 参数精确居中（推荐，PIL 8.0+）
        # 将字符绘制在临时画布中心，使用 'mm' 锚点（middle-middle）
        # try:
        #     char_draw.text((temp_size // 2, temp_size // 2), 
        #                   char, font=font, fill=random_color(20, 80), anchor='mm')
        # except TypeError:
        #     # 方法2：兼容旧版本 PIL，使用 textbbox 计算精确位置
        #     bbox = char_draw.textbbox((0, 0), char, font=font)
        #     text_width = bbox[2] - bbox[0]
        #     text_height = bbox[3] - bbox[1]
        #     x = (temp_size - text_width) // 2 - bbox[0]
        #     y = (temp_size - text_height) // 2 - bbox[1]
        #     char_draw.text((x, y), char, font=font, fill=random_color(20, 80))
        
        # 随机旋转
        angle = random.randint(-20, 20)
        rotated_char = char_img.rotate(angle, expand=False, resample=Image.BILINEAR)
        
        # 计算垂直偏移（根据新高度调整）
        y_offset = random.randint(10, 18)
        
        # 计算粘贴位置（确保字符居中显示）
        paste_x = x_offset - temp_size // 2 + char_width // 2
        paste_y = y_offset - temp_size // 2 + height // 2
        
        # 粘贴字符到主画布
        image.paste(rotated_char, (paste_x, paste_y), rotated_char)
        
        # 移动到下一个字符位置
        x_offset += char_width

    # 添加干扰线
    for _ in range(4):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line([x1, y1, x2, y2], fill=random_color(150, 220), width=random.choice([1, 2]))

    # 添加噪点
    for _ in range(50):
        x, y = random.randint(0, width), random.randint(0, height)
        draw.point((x, y), fill=random_color(100, 200))

    return captcha_text, image

def f_readLoginPublicKey():
    login_public_pem_filepath = os.path.join(g_config.uploadDir, "login_ssh_rsa", "public.pem")
    f = open(login_public_pem_filepath, 'r', encoding="utf-8")
    lines = f.readlines()
    f.close()
    loginPublicKey = ""
    for line in lines:
        line = line.strip()
        loginPublicKey = loginPublicKey + line
    return loginPublicKey

def f_readLoginPrivateKey():
    login_private_pem_filepath = os.path.join(g_config.uploadDir, "login_ssh_rsa", "private.pem")
    f = open(login_private_pem_filepath, 'r', encoding="utf-8")
    loginPrivateKey = f.read()
    f.close()
    return loginPrivateKey

def index(request):
    context = {
        "settings": f_settingsReadData()
    }
    data = []

    params = f_parseGetParams(request)

    page = params.get('p', 1)
    page_size = params.get('ps', 10)
    try:
        page = int(page)
    except:
        page = 1

    try:
        page_size = int(page_size)
        if page_size < 1:
            page_size = 1
    except:
        page_size = 10

    skip = (page - 1) * page_size
    sql_data = "select * from auth_user order by id desc limit %d,%d " % (
        skip, page_size)
    sql_data_num = "select count(id) as count from auth_user "

    count = g_database.select(sql_data_num)

    if len(count) > 0:
        count = int(count[0]["count"])
        data = g_database.select(sql_data)

    else:
        count = 0

    page_num = int(count / page_size)  # 总页数
    if count % page_size > 0:
        page_num += 1
    pageLabels = buildPageLabels(page=page, page_num=page_num)
    pageData = {
        "page": page,
        "page_size": page_size,
        "page_num": page_num,
        "count": count,
        "pageLabels": pageLabels
    }

    context["data"] = data
    context["pageData"] = pageData

    return render(request, 'app/user/index.html', context)

def add(request):
    login_user_is_superuser = False
    login_user = f_sessionReadUser(request)
    if login_user:
        login_user_is_superuser = login_user.get("is_superuser")
    if not login_user_is_superuser:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX请求返回JSON格式
            res = {
                "code": 0,
                "msg": "无权限"
            }
            return f_responseJson(res)
        else:
            return render(request, 'app/message.html',
                          {"msg": "无权限", "is_success": False, "redirect_url": "/user/index"})
    else:
        context = {
            "settings": f_settingsReadData()
        }
        if request.method == 'POST':
            __ret = False
            __msg = "未知错误"

            # 直接从request.POST获取参数，因为f_parsePostParams无法处理FormData
            username = request.POST.get("username", "").strip()
            email = request.POST.get("email", "").strip()
            password = request.POST.get("password", "").strip()
            is_active = request.POST.get("is_active")

            try:
                is_active = int(is_active)

                if username == "":
                    raise Exception("用户名不能为空")
                if email == "":
                    raise Exception("邮箱不能为空")
                if len(password) < 6 or len(password) > 16:
                    raise Exception("密码的长度需满足6-16位")

                user = User.objects.filter(username=username)
                if len(user) > 0:
                    raise Exception("用户名已存在")
                else:
                    now = datetime.now()
                    user = User()
                    user.username = username
                    user.set_password(password)
                    user.email = email
                    user.date_joined = now
                    user.is_superuser = 0  # 表单创建均为非超级管理员
                    user.is_staff = 1
                    user.is_active = is_active
                    user.save()

                    if user.id > 0:
                        __ret = True
                        __msg = "添加成功"
                    else:
                        __msg = "添加失败"

            except Exception as e:
                __msg = str(e)

            # 检查请求头，判断是否为AJAX请求
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # AJAX请求返回JSON格式
                res = {
                    "code": 1000 if __ret else 0,
                    "msg": __msg
                }
                return f_responseJson(res)
            else:
                # 普通请求重定向
                if __ret:
                    redirect_url = "/user/index"
                else:
                    redirect_url = "/user/add"
                return render(request, 'app/message.html',
                              {"msg": __msg, "is_success": __ret, "redirect_url": redirect_url})
        else:
            context["user"] = {
                "is_active": 1,
            }
            context["handle"] = "add"
            return render(request, 'app/user/add.html', context)

# 获取用户详情API

def api_openUserDetail(request):
    ret = False
    msg = "未知错误"
    data = {}
    if request.method == 'GET':
        try:
            login_user = f_sessionReadUser(request)
            if not login_user:
                raise Exception("未登录")
            login_user_is_superuser = login_user.get("is_superuser")
            if not login_user_is_superuser:
                raise Exception("无权限")

            user_id = request.GET.get("id")
            if user_id:
                user = User.objects.filter(id=int(user_id)).first()
                if user:
                    # 将用户对象转换为字典
                    data = {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'is_active': user.is_active,
                        'is_superuser': user.is_superuser,
                    }
                    ret = True
                    msg = "success"
                else:
                    msg = "the data does not exist"
            else:
                msg = "id is required"
        except Exception as e:
            msg = str(e)
    else:
        msg = "request method not supported"
    
    res = {
        "code": 1000 if ret else 0,
        "msg": msg,
        "data": data
    }
    g_logger.info("UserView.api_openUserDetail() res:%s" % str(res))
    return f_responseJson(res)

def edit(request):
    login_user_is_superuser = False
    login_user = f_sessionReadUser(request)
    if login_user:
        login_user_is_superuser = login_user.get("is_superuser")

    if not login_user_is_superuser:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX请求返回JSON格式
            res = {
                "code": 0,
                "msg": "无权限"
            }
            return f_responseJson(res)
        else:
            return render(request, 'app/message.html',
                          {"msg": "无权限", "is_success": False, "redirect_url": "/user/index"})
    else:

        context = {
            "settings": f_settingsReadData()
        }

        if request.method == 'POST':
            __ret = False
            __msg = "未知错误"
            
            # 直接从request.POST获取参数，因为f_parsePostParams无法处理FormData
            handle = request.POST.get("handle", "")
            user_id = request.POST.get("id")  # 被操作用户id
            is_active = request.POST.get("is_active")
            username = request.POST.get("username", "").strip()
            email = request.POST.get("email", "").strip()
            new_password = request.POST.get("new_password", "")
            re_password = request.POST.get("re_password", "")

            try:
                user_id = int(user_id)
                is_active = int(is_active)

                if username == "":
                    raise Exception("用户名不能为空")
                if email == "":
                    raise Exception("邮箱不能为空")
                if re_password == "" and new_password == "":
                    pass
                    # 未修改密码
                else:
                    # 修改了密码

                    if new_password == "":
                        raise Exception("新密码不能为空")
                    if re_password == "":
                        raise Exception("确认新密码不能为空")
                    if new_password != re_password:
                        raise Exception("两次输入的密码不一致")
                    if len(new_password) < 6 or len(new_password) > 16:
                        raise Exception("新密码的长度需满足6-16位")

                user = User.objects.filter(id=user_id)
                if len(user) > 0:
                    user = user[0]

                    # 验证要修改的用户名是否已经存在start
                    if user.username == username:
                        pass
                        # 用户名未做修改
                    else:
                        filter_username = g_database.select(
                            "select count(1) as count from auth_user where id!=%d and username='%s'" % (
                            user_id, username))
                        filter_username_count = int(filter_username[0]["count"])
                        if filter_username_count > 0:
                            raise Exception("新用户名已经存在！")
                        user.username = username  # 修改了用户名
                    # 验证要修改的用户名是否已经存在end

                    if re_password == "" and new_password == "":
                        pass
                    else:
                        user.set_password(new_password)  # 修改了密码

                    user.email = email
                    user.is_active = is_active
                    user.save()
                    __ret = True
                    __msg = "编辑成功"

                    context["user"] = user
                else:
                    raise Exception("该数据不存在！")
            except Exception as e:
                __msg = str(e)

            # 检查请求头，判断是否为AJAX请求
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # AJAX请求返回JSON格式
                res = {
                    "code": 1000 if __ret else 0,
                    "msg": __msg
                }
                g_logger.info("UserView.edit() ajax res:%s" % str(res))
                return f_responseJson(res)
            else:
                # 普通请求重定向
                if __ret:
                    redirect_url = "/user/index"
                else:
                    redirect_url = "/user/edit?id=" + str(user_id)
                g_logger.info("UserView.edit() ret=%d,msg=%s" % (__ret, __msg))
                return render(request, 'app/message.html',
                              {"msg": __msg, "is_success": __ret, "redirect_url": redirect_url})

        else:
            params = f_parseGetParams(request)
            user_id = params.get("id")
            if user_id:
                user = User.objects.filter(id=user_id)
                if len(user) > 0:
                    user = user[0]
                    context["handle"] = "edit"
                    context["user"] = user
                    return render(request, 'app/user/add.html', context)
                else:
                    return render(request, 'app/message.html',
                                  {"msg": "该用户不存在", "is_success": False, "redirect_url": "/user/index"})

            else:
                return redirect("/user/index")

def api_postDel(request):
    ret = False
    msg = "未知错误"
    if request.method == 'POST':
        params = f_parsePostParams(request)
        try:
            login_user = f_sessionReadUser(request)
            if not login_user:
                raise Exception("未登录")
            login_user_is_superuser = login_user.get("is_superuser")
            if not login_user_is_superuser:
                raise Exception("无权限")

            user_id = int(params.get("id"))
            if not user_id:
                raise Exception("参数不合法")

            login_user_id = int(login_user.get("id"))
            if login_user_id == user_id:
                raise Exception("超级管理员不允许删除自己的账号")

            user = User.objects.filter(id=user_id)
            if len(user) > 0:
                user = user[0]
                if user.is_superuser == 1:
                    raise Exception("超级管理员不允许被删除！")
                else:
                    if user.delete():
                        ret = True
                        msg = "删除成功"
                    else:
                        msg = "删除失败！"
            else:
                raise Exception("该数据不存在！")
        except Exception as e:
            msg = str(e)
    else:
        msg = "request method not supported！"

    res = {
        "code": 1000 if ret else 0,
        "msg": msg
    }
    return f_responseJson(res)

def captcha(request):
    """生成验证码图片视图"""
    # 生成验证码
    text,image = generate_secure_captcha()

    # 存储到session
    cur_timestamp = int(time.time())
    request.session[g_session_key_captcha] = {
        "captcha_text": text,
        "captcha_create_timestamp": cur_timestamp,  # 创建秒级时间戳
    }

    print("captcha_text:%s" % text)

    # 创建内存流输出
    stream = BytesIO()
    image.save(stream, 'PNG')
    return HttpResponse(stream.getvalue(), content_type='image/png')

def login(request):
    context = {
        "settings": f_settingsReadData()
    }

    if request.method == 'POST':
        ret = False
        msg = "未知错误"

        params = f_parsePostParams(request)

        username_s = params.get("username_s", None)
        password_s = params.get("password_s", None)
        captcha = params.get("captcha", None)

        try:

            if g_config.isEnableLoginCaptcha:
                if not captcha:
                    raise Exception("请求参数缺少验证码")
                # 开启了登录验证码功能
                session_captcha = request.session.get(g_session_key_captcha, None)
                if not session_captcha:
                    raise Exception("未发现验证码信息")

                if session_captcha:
                    captcha_text = session_captcha.get("captcha_text", "")
                    captcha_create_timestamp = session_captcha.get("captcha_create_timestamp", 0)
                    cur_timestamp = int(time.time())

                    # 验证码过期判断
                    if (cur_timestamp - captcha_create_timestamp) > 300:
                        raise Exception("验证码超过5分钟,已失效")

                    # 验证码相同判断
                    if captcha_text != captcha:
                        raise Exception("验证码不正确")


            if username_s and password_s:
                loginPrivateKey = f_readLoginPrivateKey()

                username = xc_decrypt(loginPrivateKey,username_s)
                password = xc_decrypt(loginPrivateKey,password_s)
                user = User.objects.filter(username=username)
                if len(user) > 0:
                    user = user[0]
                    if user.is_active:
                        if user.check_password(password):
                            user.first_name = "cec=0"
                            user.last_login = datetime.now()
                            user.save()
                            request.session[g_session_key_user] = {
                                "id": user.id,
                                "username": username,
                                "email": user.email,
                                "is_superuser": user.is_superuser,
                                "is_active": user.is_active,
                                "is_staff": user.is_staff,
                                # "last_login": user.last_login.strftime("%Y-%m-%d %H:%M:%S")
                            }
                            ret = True
                            msg = "登录成功"
                        else:
                            continuous_error_count = 0
                            try:
                                vals = user.first_name.split(",")
                                for val in vals:
                                    array = val.split("=")
                                    if len(array) == 2:
                                        if array[0] == "cec":
                                            continuous_error_count = int(array[1])  # v4.643开始，将first_name作为连续登录失败的次数
                            except:
                                pass

                            continuous_error_count += 1
                            if continuous_error_count > 6:
                                is_active = False
                                msg = "密码错误，连续失败第%d次，账号锁定"%continuous_error_count
                            else:
                                is_active = True
                                msg = "密码错误，连续失败第%d次" % continuous_error_count
                            user.is_active = is_active
                            user.first_name = "cec=%d"%continuous_error_count
                            user.save()
                    else:
                        msg = "账号已锁定"
                else:
                    msg = "用户名未注册"
            else:
                msg = "请求参数不合法"
                
        except Exception as e:
            msg = str(e)


        res = {
            "code": 1000 if ret else 0,
            "msg": msg
        }
        return f_responseJson(res)
    else:
        loginPublicKey = f_readLoginPublicKey()
        context["loginPublicKey"] = loginPublicKey
        context["isEnableLoginCaptcha"] = 1 if g_config.isEnableLoginCaptcha else 0
        return render(request, 'app/user/login.html', context)

def logout(request):
    f_sessionLogout(request)
    return redirect("/")
