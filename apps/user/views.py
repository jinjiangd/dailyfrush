from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
from user.models import User
from django.http import HttpResponse
from django.conf import settings
from django.core.mail import send_mail
from celery_tasks.tasks import send_register_active_email
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import check_password


from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
import re
# Create your views here.


# 使用类视图进行注册
# /user/register
class RegisterView(View):
    '''注册'''
    def get(self, request):
        '''显示注册页面'''
        return render(request, 'register.html')

    def post(self, request):
        '''注册处理'''
        # 接受数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 数据校验
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '无效的邮箱'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None

        if user:
            # 用户名存在
            return render(request, 'register.html', {'errmsg': '用户名已存在'})

        # 注册处理
        user = User.objects.create_user(username, email, password)
        # 默认不激活用户
        user.is_active = 0
        user.save()

        # 发送激活邮件，包含激活链接： http://127.0.0.1:8000/user/active/1
        # 激活链接中需要包含用户的身份信息,并把身份信息加密
        # 加密用户的身份信息，生成激活token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info).decode('utf-8')

        # 发送邮件
        send_register_active_email.delay(email, username, token)

        # 返回应答
        return redirect(reverse('goods:index'))


# /user/active
class ActiveView(View):
    '''用户激活'''
    def get(self, request, token):
        '''用户激活'''
        # 进行解密，获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 获取用户id
            user_id = info['confirm']
            # 根据用户id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            # 返回登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活链接已过期
            return HttpResponse('激活链接已过期')


# /user/login
class LoginView(View):
    '''登录'''
    def get(self, request):
        # 判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        # 接受数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        # 校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '账号不存在'})

        """
        # 业务处理：登录校验 django 1.0版本
        user = authenticate(username=username, password=password)
        print(user)
        if user is not None:
            # 用户名密码正确
            if user.is_active:
                # 用户已激活
                # 记录用户的登录状态
                login(request, user)
                # 跳转到首页
                return redirect(reverse('goods:index'))
            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg': '用户未激活'})
        else:
            # 用户名密码不正确
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})
        """

        # 业务处理：登录校验 django 2.0版本

        # 跳转到首页
        response = redirect(reverse('goods:index'))
        # 判断是否记住用户名
        remember = request.POST.get('remember')
        if remember == 'on':
            # 记住用户名
            response.set_cookie('username', username, max_age=7*24*3600)
        else:
            # 删除cookie中保存的用户名
            response.delete_cookie('username')


        try:
            user = User.objects.get(username=username)
            pwd = user.password

            if check_password(password, pwd):
                # 用户名密码正确
                if user.is_active:
                    # 用户已激活
                    # 记录用户的登录状态
                    login(request, user)

                    # 返回response
                    return response
                else:
                    # 用户未激活
                    return render(request, 'login.html', {'errmsg': '用户未激活'})
            else:
                # 用户名密码不正确
                return render(request, 'login.html', {'errmsg': '用户名或密码错误'})
        except User.DoesNotExist:
            return render(request, 'login.html', {'errmsg': '服务器异常'})


# /user
class UserInfoView(View):
    '''用户中心-信息页'''
    def get(self, request):
        '''显示'''
        return render(request, 'user_center_info.html', {'page': 'user'})


# /user/order
class UserOrderView(View):
    '''用户中心-订单页'''
    def get(self, request):
        '''显示'''
        return render(request, 'user_center_order.html', {'page': 'order'})


# /user/address
class AddressView(View):
    '''用户中心-地址页'''
    def get(self, request):
        '''显示'''
        return render(request, 'user_center_site.html', {'page': 'address'})


