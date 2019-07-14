# 使用celery
from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
import time


# 如果使用的 celery worker 则需要配置下面信息
# import os
# import django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfrush.settings')
# django.setup()


# 创建一个Celery类的实例对象
app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/8')

# 定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
    '''发送激活邮件'''
    # 组织邮件信息
    subject = '欢迎信息'
    message = ''
    sender = settings.EMAIL_FROM
    receive = [to_email]
    html_message = '<h1>%s,欢迎成为会员</h1>请点击下面链接激活您的账户:<br/><a href="http://127.0.0.1:8000/user/active/%s"> http://127.0.0.1:8000/user/active/%s </a>' % (
    username, token, token)
    # 发送邮件
    send_mail(subject, message, sender, receive, html_message=html_message)
    time.sleep(5)

