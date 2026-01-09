from datetime import datetime
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
import re
from http.client import responses
from django.core.paginator import Paginator, EmptyPage
from django.utils import timezone
from random import randint
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import DataError
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseRedirect, \
    HttpResponseServerError
from django.shortcuts import render, redirect
from django.template.context_processors import request
from django.views import View
from django_redis import get_redis_connection
from redis.commands.json import JSON
from home.models import CityCategory, City, CityImage, RealEstateAgent, Transaction, ChatMessage
from users.models import User
from libs.captcha.captcha import captcha
from libs.yuntongxun.sms import CCP
from utils.json_encoder import serialize_with_datetime
from utils.response_code import RETCODE
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from django.urls import reverse
from django.contrib import messages

# Create your views here.
class RegisterView(View):
    """用户的视图返回"""
    def get(self,request):
        return render(request,'register.html')

    # 注册功能
    def post(self,request):
        """
        1.接受前端传递过来的参数
        2.验证参数
            2.1参数是否齐全
            2.2手机号码格式是否正确
            2.3密码是否格式正确
            2.4密码和确认密码是否完全一致
            2.5短信验证码是否和redis缓存一致
        3.保存注册信息
        4.返回响应跳转指定页面
        ：:param
        ：return
        """

            # 1.接受前端传递过来的参数
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        smscode = request.POST.get('sms_code')
            # 2.验证参数
            #     2.1参数是否齐全
        if not all([mobile,password,password2,smscode]):
            return HttpResponseBadRequest('缺少必传参数...')
            #     2.2手机号码格式是否正确
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return HttpResponseBadRequest('请输入正确的手机号码...')
            #     2.3密码是否格式正确,是否为8-20个数字和字母
        if not re.match(r'^[0-9A-Za-z]{8,20}$',password):
            return HttpResponseBadRequest('请输入8-20的密码，密码是数字或字母')
            #     2.4密码和确认密码是否完全一致
        if password != password2:
            return HttpResponseBadRequest('两次输入的密码不一致')
            #     2.5短信验证码是否和redis缓存一致
        redis_conn = get_redis_connection('default')
        redis_sms_code = redis_conn.get('sms:%s'%mobile)
        if redis_sms_code is None:
            return HttpResponseBadRequest('短信验证码已过期！')
        #转换成字符串
        if smscode != redis_sms_code.decode():
            return HttpResponseBadRequest('短信验证码错误')

            # 3.保存注册信息
        try:
            # 检查是否有中介相关参数
            is_agent = request.POST.get('is_agent', True)  # 如果有中介注册选项
            user = User.objects.create_user(
                username=mobile,
                mobile=mobile,
                password=password,
                is_real_estate_agent=is_agent  # 设置中介标志
            )
        except DataError as e:
            logger.error(e)
            return HttpResponseBadRequest('注册失败！')

        from django.contrib.auth import login

        login(request,user)
        responses = redirect(reverse('home:index'))
        responses.set_cookie('is_login',True)
        responses.set_cookie('username',user.username,max_age=7*24*3600)
        return responses
            # 4.返回响应跳转指定页面
            # ：:param
            # ：return
        #redirect表示重定向，reverse表示通过namespace：name获得视图所对应的路由



#获取图形验证码Get请求
class ImageCodeView(View):
    def get(self,request):
        #1.获取前端传递过来的参数uuid
        uuid = request.GET.get('uuid')
        #2.判断uuid是否为空
        if uuid is None:
            return HttpResponse('未获取到请求参数~~~~~~')
        #3.通过调用captcha来生成图形验证码
        #1、验证码内容 2、验证码图形的二进制
        text,image = captcha.generate_captcha()
        #4.将图片验证码内容保存到redis当中，并且设置过期时间
        #使用uuid作为键，图形验证码作为值
        redis_conn = get_redis_connection('default')
        #key设置为uuid：即imgxxxx
        #设置过期时间300
        redis_conn.setex('img:%s'%uuid,300,text)

        #返回响应（图片二进制内容）
        #将生成的图片以context_type为img/jpeg的形式返回给浏览器
        return HttpResponse(image,content_type='image/jpeg')

import logging
#获取django默认的日志记录器
logger = logging.getLogger('django')

class SmsCodeView(View):
    """短信验证码的视图"""


    def get(self,request):
        """处理get请求"""
        #1.接收前段传递的参数
        mobile = request.GET.get('mobile')#接收短信的手机号码
        image_code = request.GET.get('image_code')#用户输入的图形验证码
        uuid = request.GET.get('uuid')#图形验证码的唯一标识

        #2.校验参数的完整性
        if not all([mobile,image_code,uuid]):
            #若任意参数缺失,返回一个错误的响应（字典数据）
            return JsonResponse({'code':RETCODE.NECESSARYPARAMERR,'errmsg':'缺少必传的参数'})

        #3.链接redis的数据库，获取图形的验证码
        #连接redis默认的0号库
        redis_conn = get_redis_connection('default')
        redis_image_code = redis_conn.get('img:%s'%uuid)#获取通过键获取图形验证码的值

        #4.检查图形验证码是否过期
        if redis_image_code is None:
            return JsonResponse({'code':RETCODE.IMAGECODEERR,'errmsg':'图形验证码失效'})

        #5.删除已经使用的图形验证码（防止重复验证）
        try:
            redis_conn.delete('img:%s'%uuid)
        except Exception as e:
            logger.error(f"删除redis图形验证码失败:{e}")#记录错误日志

        #6.比对图形验证码（忽略大小写且redis中的数据是byte类型）
        redis_image_code = redis_image_code.decode()#将bytes转为字符串
        if image_code.lower() != redis_image_code.lower():
            return JsonResponse({'code':RETCODE.IMAGECODEERR,'errmsg':'输入的图形验证码有误'})

        #7.生成6位随机的短信验证码
        sms_code = '%04d' %randint(0,9999)

        #8.记录验证码的日志（仅用于开发调试，生产场景建议移除）
        logger.info(f"短信验证码:{sms_code}")

        #9.将短信验证码存入redis
        #键的格式：sms：手机号码，值：验证码，过期时间300秒
        redis_conn.setex('sms:%s'%mobile,300,sms_code)

        #10.调用云通讯sdk发送短信
        CCP().send_template_sms(mobile,[sms_code,5],1)

        #11.发送成功响应
        return JsonResponse({'code':RETCODE.OK,'errmsg':'发送短信成功'})

class LoginView(View):
    def get(self,request):

        return render(request,'login.html')
    def post(self,request):
        # 1、接收参数
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        # 2、参数的验证
        if not all([mobile,password]):
            return HttpResponseBadRequest('缺少必传参数')

        # 2.1
        #     验证手机号是否符合规则
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return HttpResponseBadRequest('请输入一个正确的手机号')
        # 2.2
        #     验证密码是否符合规则
        if not re.match(r'^[0-9A-Za-z]{8,20}$',password):
            return HttpResponseBadRequest('密码为8-20位')

        #
        # 3、用户认证登录
        from django.contrib.auth import authenticate
        user = authenticate(mobile=mobile,password=password)

        if user is  None:
            return HttpResponseBadRequest('用户名称|密码错误')
        # 4、状态的保持
        from django.contrib.auth import login
        login(request,user)

        # 5、根据用户角色进行差异化跳转
        next_page = request.GET.get('next') or reverse('users:agent_center')  # 直接跳转到中介中心

        responses = redirect(next_page)

        #有next查询字符串则跳转至个人中心，没有next则跳转至首页
        #根据next参数进行页面的跳转

        # next_page = request.GET.get('next')
        # if next_page:
        #     responses  = redirect(next_page)
        # else:
        #     responses = redirect(reverse('home:index'))

        # 5、根据用户选择的是否记录登录状态
        if remember != 'on':#没有勾选用户信息，则浏览器会话结束
            request.session.set_expiry(0)
            responses.set_cookie('is_login',True)
            responses.set_cookie('username',user.username,max_age=30*24*3600)
        else:
            #勾选了记住用户，None表示两周以后过期
            request.session.set_expiry(None)
            responses.set_cookie('is_login', True,max_age=14*24*3600)
            responses.set_cookie('username', user.username, max_age=30 * 24 * 3600)
        # 6、为了首页现实需要设置一些cookie信息
        return responses
class LogoutView(View):
    #退出登录
    def get(self,request):
        #清理session中的数据
        logout(request)
        #退出登录，重定向到登录界面
        responses = redirect(reverse('home:index'))
        #退出登录时，清除cookie中的信息
        responses.delete_cookie('is_login')
        return responses

#忘记密码
class ForgetPasswordView(View):
    def get(self,request):
        return render(request,'forget_password.html')

    def post(self,request):
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        smscode = request.POST.get('sms_code')
        # 2.验证参数
        #     2.1参数是否齐全
        if not all([mobile, password, password2, smscode]):
            return HttpResponseBadRequest('缺少必传参数...')
             #     2.2手机号码格式是否正确
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('请输入正确的手机号码...')
                #     2.3密码是否格式正确,是否为8-20个数字和字母
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseBadRequest('请输入8-20的密码，密码是数字或字母')
                #     2.4密码和确认密码是否完全一致
        if password != password2:
            return HttpResponseBadRequest('两次输入的密码不一致')
                #     2.5短信验证码是否和redis缓存一致
        redis_conn = get_redis_connection('default')
        redis_sms_server = redis_conn.get('sms:%s' % mobile)
        if redis_sms_server is None:
            return HttpResponseBadRequest('短信验证码已过期！')
        # 转换成字符串
        if smscode != redis_sms_server.decode():
            return HttpResponseBadRequest('短信验证码错误')

                # 3.保存注册信息
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            #如果该手机号码不存在，新用户的注册操作
            try:
                User.objects.create_user(username=mobile,password=password,mobile=mobile)
            except Exception:
                return HttpResponseBadRequest('修改失败请稍后再试')

        else:
            #如果该手机号查到用户信息，则去修改密码

            user.set_password(password)
            user.save()

            responses = redirect(reverse('users:login'))
            return responses

class WriteBlogView(LoginRequiredMixin,View):
    def get(self,request):
        #获取博客分类信息
        categories = CityCategory.objects.all()
        agents = RealEstateAgent.objects.filter(is_active=True)  # 获取活跃中介
        context = {
            'categories':categories,
            'agents': agents,  # 传递中介列表
        }
        return render(request,'write_blog.html',context=context)

    def post(self,request):
        avatar = request.FILES.get('avatar')
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        decoration = request.POST.get('decoration')
        min_price = request.POST.get('min_price')
        description = request.POST.get('description')


        # max_price = request.POST.get('max_price')
        user = request.user



        if not all([title,category_id,decoration,min_price,description]):
            return HttpResponseBadRequest('参数不齐全')
        try:
            category = CityCategory.objects.get(id=category_id)
        except CityCategory.DoesNotExist:
            return HttpResponseBadRequest('没有此分类')
        category = CityCategory.objects.get(id=category_id)

        agent_id = request.POST.get('agent')  # 获取选择的中介
        agent = None
        if agent_id:
            try:
                agent = RealEstateAgent.objects.get(id=agent_id)
            except RealEstateAgent.DoesNotExist:
                pass
        # try:
        article = City.objects.create(
            author=user,
            avatar=avatar,
            description=description,
            decoration=decoration,
            min_price=min_price,
            category=category,
            title=title,
            agent=agent

        )
        images = request.FILES.getlist('images')  # 获取多张图片
        for img in images:
            CityImage.objects.create(city=article, image=img)

        return redirect(reverse('home:detail', kwargs={'id': article.id}))
        # except Exception as e:
        #     logger.error(e)
        #     return HttpResponseBadRequest('发布失败')
        return redirect(reverse('home:index'))
class UserCenterView(LoginRequiredMixin,View):
    def get(self,request):
        users = request.user
        # cat_id = request.GET.get('cat_id', 1)
        # category = CityCategory.objects.get(id=cat_id)
        purchase_requests = City.objects.filter(author=users)
        context = {
            'username':users.username,
            'mobile':users.mobile,
            'purchases_requests': purchase_requests,
            'avatar':users.avatar.url if users.avatar else None,
            'user_desc':users.description,
        }
        return render(request, 'center.html',context=context)

    def post(self,request):
        #获取用户之前的信息
        user = request.user
        #1、接收参数
        username = request.POST.get('username',user.username)
        user_desc = request.POST.get('desc',user.description)
        avatar = request.FILES.get('avatar')
        #2、将参数保存
        try:
            user.username = username
            user.description = user_desc
            if avatar:
                user.avatar = avatar
            user.save()
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('修改失败')
        #4、刷新当前页面
        response = redirect(reverse('users:center'))
        #3、更新cookie为username信息
        response.set_cookie('username',user.username,max_age=14*24*3600)
        #5、返回响应
        return response


class DeleteCityView(LoginRequiredMixin, View):
    def post(self, request):
        # 1. 获取前端传的文章ID
        article_id = request.POST.get('id')
        # 2. 校验ID是否是数字
        if not article_id or not article_id.isdigit():
            return HttpResponseBadRequest('无效的文章ID')
        # 3. 找文章 + 校验权限（只能删自己的）
        try:
            article = City.objects.get(id=article_id)
            if article.author != request.user:
                return HttpResponseBadRequest('你没权限删这篇文章！')
            # 4. 删除文章
            article.delete()
        except City.DoesNotExist:
            return HttpResponseBadRequest('这篇文章不存在！')
        # 5. 删除成功跳回首页
        return redirect(reverse('home:index'))


class DeleteArticleView(LoginRequiredMixin, View):
    def post(self, request):
        # 1. 获取前端传的文章ID
        article_id = request.POST.get('id')
        # 2. 校验ID是否是数字
        if not article_id or not article_id.isdigit():
            return HttpResponseBadRequest('无效的文章ID')
        # 3. 找文章 + 校验权限（只能删自己的）
        try:
            article = City.objects.get(id=article_id)
            if article.author != request.user:
                return HttpResponseBadRequest('你没权限删这篇文章！')
            # 4. 删除文章
            article.delete()
        except City.DoesNotExist:
            return HttpResponseBadRequest('这篇文章不存在！')
        # 5. 删除成功跳回首页
        return redirect(reverse('home:index'))


class DeletePurchaseRequestView(LoginRequiredMixin, View):
    def post(self, request):
        # 1. 获取前端传的求购信息ID
        request_id = request.POST.get('id')
        user = request.user
        print(user.description)
        # 2. 校验ID是否是数字
        if not request_id or not request_id.isdigit():
            return HttpResponseBadRequest('无效的求购信息ID')

        # 3. 找求购信息 + 校验权限（只能删自己的）
        try:
            purchase_request = City.objects.get(id=request_id)
            if purchase_request.author != user:
                return HttpResponseBadRequest('你没权限删这条信息！')
            # 4. 删除求购信息
            purchase_request.delete()
        except City.DoesNotExist:
            return HttpResponseBadRequest('这条求购信息不存在！')

        # 5. 删除成功跳回个人信息页面
        return redirect(reverse('users:center'))


class AgentManagementView(UserPassesTestMixin, View):
    """
    中介管理视图 - 仅超级管理员可访问
    """

    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request):
        agents = RealEstateAgent.objects.all()
        context = {
            'agents': agents
        }
        return render(request, 'admin/agent_management.html', context)

    def post(self, request):
        # 创建中介用户
        username = request.POST.get('username')
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        license_number = request.POST.get('license_number')
        company = request.POST.get('company')
        phone = request.POST.get('phone')

        if not all([username, mobile, password, license_number, company, phone]):
            return HttpResponseBadRequest('缺少必填字段')

        # 检查用户是否已存在
        if User.objects.filter(mobile=mobile).exists():
            return HttpResponseBadRequest('该手机号已存在')

        # 创建用户
        user = User.objects.create_user(
            username=username,
            mobile=mobile,
            password=password,
            is_real_estate_agent=True
        )

        # 创建中介资料
        RealEstateAgent.objects.create(
            user=user,
            license_number=license_number,
            company=company,
            phone=phone
        )

        return redirect('users:agent_management')


class AgentDetailView(UserPassesTestMixin, View):
    """
    中介详情视图
    """

    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, agent_id):
        agent = get_object_or_404(RealEstateAgent, id=agent_id)
        context = {
            'agent': agent
        }
        return render(request, 'admin/agent_detail.html', context)



# users/views.py - 添加中介视图
class AgentCenterView(LoginRequiredMixin, View):
    """
    中介个人中心
    """

    def get(self, request):
        # 先检查用户是否为中介
        # if not request.user.is_real_estate_agent:
        #     return render(request, 'not_agent.html', {
        #         'error_message': '您不是注册的房屋中介，无法访问此页面'
        #     })

            # 尝试获取中介资料，如果不存在则创建
        try:
            agent_profile, created = RealEstateAgent.objects.get_or_create(
                user=request.user,
                defaults={
                    'license_number': request.user.agent_license or f'DEFAULT_{request.user.id}',
                    'company': request.user.agent_company or '默认中介公司',
                    'phone': request.user.agent_phone or request.user.mobile
                }
            )
        except:
            # return render(request, 'not_agent.html', {
            #     'error_message': '中介资料获取失败，请联系管理员'
            # })
            agent_profile = RealEstateAgent.objects.create(
                user=request.user,
                license_number=f'DEFAULT_{request.user.id}',
                company='默认中介公司',
                phone=request.user.mobile
            )
        transactions = Transaction.objects.filter(agent=agent_profile).order_by('-created_at')
        context = {
            'agent_profile': agent_profile,
            'user': request.user,
            'transactions': transactions
        }
        return render(request, 'agent_center.html', context)

    def post(self, request):
        # 检查用户是否为中介
        # if not request.user.is_real_estate_agent:
        #     return redirect('users:center')
        #
        # try:
        #     agent_profile = request.user.agent_profile
        # except RealEstateAgent.DoesNotExist:
        #     return redirect('users:center')

        # 更新用户信息
        request.user.username = request.POST.get('username', request.user.username)
        request.user.description = request.POST.get('description', request.user.description)
        avatar = request.FILES.get('avatar')
        if avatar:
            request.user.avatar = avatar

        agent_profile, created = RealEstateAgent.objects.get_or_create(
            user=request.user,
            defaults={
                'license_number': f'DEFAULT_{request.user.id}',
                'company': '默认中介公司',
                'phone': request.user.mobile
            }
        )

        # 更新中介信息
        agent_profile.company = request.POST.get('company', agent_profile.company)
        agent_profile.phone = request.POST.get('phone', agent_profile.phone)
        agent_profile.description = request.POST.get('description', agent_profile.description)

        request.user.save()
        agent_profile.save()

        return redirect('users:agent_center')


class AgentContractView(LoginRequiredMixin, View):
    """
    中介合同生成页面
    """

    def get(self, request):
        # 检查用户是否为中介
        # if not request.user.is_real_estate_agent:
        #     return redirect('users:center')
        #
        # try:
        #     agent_profile = request.user.agent_profile
        # except RealEstateAgent.DoesNotExist:
        #     return render(request, 'not_agent.html', {
        #         'error_message': '中介资料不完整，请联系管理员'
        #     })
        agent_profile, created = RealEstateAgent.objects.get_or_create(
            user=request.user,
            defaults={
                'license_number': f'DEFAULT_{request.user.id}',
                'company': '默认中介公司',
                'phone': request.user.mobile
            }
        )

        context = {
            'agent_profile': agent_profile
        }
        return render(request, 'agent_contract.html', context)

    def post(self, request):
        # 检查用户是否为中介
        # if not request.user.is_real_estate_agent:
        #     return redirect('users:center')

        # 处理合同生成逻辑
        # 这里可以保存合同信息到数据库
        return redirect('users:agent_contracts')


class AgentTransactionView(LoginRequiredMixin, View):
    """
    中介交易记录页面
    """
    def get(self, request):
        # 检查用户是否为中介
        # if not request.user.is_real_estate_agent:
        #     return redirect('users:center')
        #
        # try:
        #     agent_profile = request.user.agent_profile
        # except RealEstateAgent.DoesNotExist:
        #     return render(request, 'not_agent.html', {
        #         'error_message': '中介资料不完整，请联系管理员'
        #     })
        agent_profile, created = RealEstateAgent.objects.get_or_create(
            user=request.user,
            defaults={
                'license_number': f'DEFAULT_{request.user.id}',
                'company': '默认中介公司',
                'phone': request.user.mobile
            }
        )

        transactions = Transaction.objects.filter(agent=agent_profile)
        context = {
            'transactions': transactions
        }
        return render(request, 'agent_transactions.html', context)



# users/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

class ChatView(LoginRequiredMixin, View):
    """
    处理聊天消息
    """
    def get(self, request):
        # 获取聊天记录
        receiver_id = request.GET.get('receiver_id')
        property_id = request.GET.get('property_id')

        messages = ChatMessage.objects.filter(
            Q(sender=request.user, receiver_id=receiver_id) |
            Q(sender_id=receiver_id, receiver=request.user)
        ).order_by('timestamp')

        if property_id:
            messages = messages.filter(property_article_id=property_id)

        messages_data = []
        for msg in messages:
            messages_data.append({
                'id': msg.id,
                'sender': msg.sender.username,
                'message': msg.message,
                'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'is_current_user': msg.sender == request.user
            })

        return JsonResponse({'messages': messages_data})

@method_decorator(csrf_exempt, name='dispatch')
class SendMessageView(LoginRequiredMixin, View):
    """
    发送消息
    """
    def post(self, request):
        data = json.loads(request.body)
        receiver_id = data.get('receiver_id')
        message = data.get('message')
        property_id = data.get('property_id')

        try:
            receiver = User.objects.get(id=receiver_id)
            property_article = City.objects.get(id=property_id) if property_id else None

            chat_message = ChatMessage.objects.create(
                sender=request.user,
                receiver=receiver,
                message=message,
                property_article=property_article
            )

            return JsonResponse({
                'success': True,
                'message_id': chat_message.id,
                'timestamp': chat_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '接收用户不存在'})
        except City.DoesNotExist:
            return JsonResponse({'success': False, 'error': '房产信息不存在'})





from django.http import HttpResponse
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
import json
from datetime import datetime
import logging
from django.db import transaction  # 事务：确保PDF生成+删除房屋原子操作
from io import BytesIO
from utils.json_serializer import serialize_data
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas  # 生成PDF用（如果用其他库，替换这个）
from reportlab.pdfbase.ttfonts import TTFont
from django.conf import settings
# 导入 ReportLab 相关模块
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import os
logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
# class GenerateContractPdfView(LoginRequiredMixin, View):
#     """
#     生成PDF合同视图 - 使用 ReportLab
#     """
#     def post(self, request):
#         try:
#             data = json.loads(request.body)
#             # 生成当前时间并转为字符串（关键修复：避免datetime对象）
#             current_datetime = datetime.now()
#             contract_data = {
#                 'property_title': data.get('property_title', ''),
#                 'property_address': data.get('property_address', ''),
#                 'property_price': float(data.get('property_price', 0)),
#                 'property_area': data.get('property_area', ''),
#                 'property_type': data.get('property_type', ''),
#                 'buyer_name': data.get('buyer_name', ''),
#                 'buyer_id_card': data.get('buyer_id_card', ''),
#                 'buyer_phone': data.get('buyer_phone', ''),
#                 'buyer_address': data.get('buyer_address', ''),
#                 'seller_name': data.get('seller_name', ''),
#                 'seller_id_card': data.get('seller_id_card', ''),
#                 'seller_phone': data.get('seller_phone', ''),
#                 'seller_address': data.get('seller_address', ''),
#                 'tax_rate': float(data.get('tax_rate', 0)),
#                 'tax_amount': float(data.get('tax_amount', 0)),
#                 'total_price': float(data.get('total_price', 0)),
#                 'created_at': current_datetime.strftime('%Y-%m-%d %H:%M:%S'),
#             }
#
#             # 获取中介信息
#             agent_profile, created = RealEstateAgent.objects.get_or_create(
#                 user=request.user,
#                 defaults={
#                     'license_number': f'DEFAULT_{request.user.id}',
#                     'company': '默认中介公司',
#                     'phone': request.user.mobile
#                 }
#             )
#
#
#             # 注册中文字体
#             font_path = os.path.join(settings.BASE_DIR, 'fonts', 'simsun.ttc')  # 即使是ttc也能通过索引指定
#             pdfmetrics.registerFont(TTFont('SIMSUN', font_path, subfontIndex=0))  # subfontIndex关键！
#             if os.path.exists(font_path):
#                 pdfmetrics.registerFont(TTFont('SimHei', font_path))
#             else:
#                 # 如果没有字体文件，使用系统字体路径
#                 try:
#                     # Windows系统
#                     pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
#                 except:
#                     # 如果没有中文字体，使用内置字体并设置fallback
#                     pass
#
#             # 创建PDF文档
#             buffer = BytesIO()
#             doc = SimpleDocTemplate(buffer, pagesize=A4)
#             elements = []
#
#             # 获取样式
#             styles = getSampleStyleSheet()
#             title_style = ParagraphStyle(
#                 'CustomTitle',
#                 parent=styles['Heading1'],
#                 fontSize=18,
#                 spaceAfter=30,
#                 alignment=1,  # 居中
#                 fontName = 'SIMSUN',  # 设置中文字体
#                 textColor = colors.black
#             )
#             heading_style = ParagraphStyle(
#                 'CustomHeading',
#                 parent=styles['Heading2'],
#                 fontSize=14,
#                 spaceAfter=12,
#                 spaceBefore=16,
#                 fontName='SIMSUN',
#                 textColor=colors.black# 设置中文字体
#             )
#             normal_style = ParagraphStyle(
#                 'CustomNormal',
#                 parent=styles['Normal'],
#                 fontName='SIMSUN',  # 设置中文字体
#                 fontSize=10,
#                 textColor=colors.black
#             )
#             # 添加标题
#             title = Paragraph("房屋买卖合同", title_style)
#             elements.append(title)
#
#             # 添加合同基本信息表格
#             contract_info_data = [
#                 ["合同编号", f"HT-{current_datetime.strftime('%Y%m%d_%H%M%S')}"],
#                 ["签订日期", current_datetime.strftime('%Y年%m月%d日')],
#             ]
#
#             contract_info_table = Table(contract_info_data, colWidths=[2*inch, 4*inch])
#             contract_info_table.setStyle(TableStyle([
#                 ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
#                 ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
#                 ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#                 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # 垂直居中
#                 ('FONTNAME', (0, 0), (-1, -1), 'SIMSUN'),  # 表格字体指定为中文字体
#                 ('FONTSIZE', (0, 0), (0, 0), 12),
#                 ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#                 ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#                 ('GRID', (0, 0), (-1, -1), 1, colors.black)
#             ]))
#             elements.append(contract_info_table)
#             elements.append(Spacer(1, 12))
#
#             # 房产信息部分
#             elements.append(Paragraph("房产信息", heading_style))
#
#             property_data = [
#                 [Paragraph("房产标题", normal_style), Paragraph(contract_data['property_title'], normal_style)],
#                 [Paragraph("房产地址", normal_style), Paragraph(contract_data['property_address'], normal_style)],
#                 [Paragraph("房产价格", normal_style),
#                  Paragraph(f"¥{contract_data['property_price']:,.2f}", normal_style)],
#                 [Paragraph("房产面积", normal_style),
#                  Paragraph(f"{contract_data['property_area']} 平方米", normal_style)],
#                 [Paragraph("房产类型", normal_style), Paragraph(contract_data['property_type'], normal_style)],
#             ]
#
#             property_table = Table(property_data, colWidths=[1.5*inch, 4*inch])
#             property_table.setStyle(TableStyle([
#                 ('GRID', (0, 0), (-1, -1), 1, colors.black),
#                 ('FONTNAME', (0, 0), (-1, -1), 'SIMSUN'),  # 表格字体
#                 ('PADDING', (0, 0), (-1, -1), 6),
#                 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#             ]))
#             elements.append(property_table)
#             elements.append(Spacer(1, 12))
#
#             # 买方信息部分
#             elements.append(Paragraph("买方信息", heading_style))
#
#             buyer_data = [
#                 [Paragraph("姓名", normal_style), Paragraph(contract_data['buyer_name'], normal_style)],
#                 [Paragraph("身份证", normal_style), Paragraph(contract_data['buyer_id_card'], normal_style)],
#                 [Paragraph("电话", normal_style), Paragraph(contract_data['buyer_phone'], normal_style)],
#                 [Paragraph("地址", normal_style), Paragraph(contract_data['buyer_address'], normal_style)],
#             ]
#
#             buyer_table = Table(buyer_data, colWidths=[1.5*inch, 4*inch])
#             buyer_table.setStyle(TableStyle([
#                 ('GRID', (0, 0), (-1, -1), 1, colors.black),
#                 ('FONTNAME', (0, 0), (-1, -1), 'SIMSUN'),
#                 ('PADDING', (0, 0), (-1, -1), 6),
#                 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#             ]))
#             elements.append(buyer_table)
#             elements.append(Spacer(1, 12))
#
#             # 卖方信息部分
#             elements.append(Paragraph("卖方信息", heading_style))
#
#             seller_data = [
#                 [Paragraph("姓名", normal_style), Paragraph(contract_data['seller_name'], normal_style)],
#                 [Paragraph("身份证", normal_style), Paragraph(contract_data['seller_id_card'], normal_style)],
#                 [Paragraph("电话", normal_style), Paragraph(contract_data['seller_phone'], normal_style)],
#                 [Paragraph("地址", normal_style), Paragraph(contract_data['seller_address'], normal_style)],
#             ]
#
#             seller_table = Table(seller_data, colWidths=[1.5*inch, 4*inch])
#             seller_table.setStyle(TableStyle([
#                 ('GRID', (0, 0), (-1, -1), 1, colors.black),
#                 ('FONTNAME', (0, 0), (-1, -1), 'SIMSUN'),
#                 ('PADDING', (0, 0), (-1, -1), 6),
#                 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#             ]))
#             elements.append(seller_table)
#             elements.append(Spacer(1, 12))
#
#             # 价格信息部分
#             elements.append(Paragraph("交易金额信息", heading_style))
#
#             price_data = [
#                 [Paragraph("房产价格", normal_style),
#                  Paragraph(f"¥{contract_data['property_price']:,.2f}", normal_style)],
#                 [Paragraph("税率", normal_style), Paragraph(f"{contract_data['tax_rate']}%", normal_style)],
#                 [Paragraph("税费", normal_style), Paragraph(f"¥{contract_data['tax_amount']:,.2f}", normal_style)],
#                 [Paragraph("总价", normal_style), Paragraph(f"¥{contract_data['total_price']:,.2f}", normal_style)],
#             ]
#
#             price_table = Table(price_data, colWidths=[1.5*inch, 4*inch])
#             price_table.setStyle(TableStyle([
#                 ('GRID', (0, 0), (-1, -1), 1, colors.black),
#                 ('FONTNAME', (0, 0), (-1, -1), 'SIMSUN'),
#                 ('PADDING', (0, 0), (-1, -1), 6),
#                 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#             ]))
#             elements.append(price_table)
#             elements.append(Spacer(1, 24))
#
#             # 签名区域
#             elements.append(Paragraph("签字确认", heading_style))
#
#             signature_data = [
#                 [Paragraph("买方签字:", normal_style), Paragraph("_____________________", normal_style),
#                  Paragraph("日期:", normal_style), Paragraph("___________", normal_style)],
#                 ["", "", "", ""],
#                 [Paragraph("卖方签字:", normal_style), Paragraph("_____________________", normal_style),
#                  Paragraph("日期:", normal_style), Paragraph("___________", normal_style)],
#                 ["", "", "", ""],
#                 [Paragraph("中介签字:", normal_style), Paragraph("_____________________", normal_style),
#                  Paragraph("日期:", normal_style), Paragraph("___________", normal_style)],
#             ]
#             signature_table = Table(signature_data, colWidths=[1.2*inch, 2*inch, 1*inch, 1.5*inch])
#             signature_table.setStyle(TableStyle([
#                 ('GRID', (0, 0), (-1, -1), 0, colors.white),
#                 ('FONTNAME', (0, 0), (-1, -1), 'SIMSUN'),
#                 ('VALIGN', (0, 0), (-1, -1), 'TOP'),
#             ]))
#             elements.append(signature_table)
#
#
#
#
#             # 构建PDF
#             doc.build(elements)
#
#             # 获取PDF内容
#             pdf_content = buffer.getvalue()
#             buffer.close()
#
#             # 创建交易记录
#             from home.models import Transaction
#             transaction = Transaction.objects.create(
#                 agent=agent_profile,
#                 property_title=contract_data['property_title'],
#                 property_address=contract_data['property_address'],
#                 property_price=contract_data['property_price'],
#                 buyer_name=contract_data['buyer_name'],
#                 buyer_phone=contract_data['buyer_phone'],
#                 seller_name=contract_data['seller_name'],
#                 seller_phone=contract_data['seller_phone'],
#                 amount=contract_data['total_price'],
#                 status='completed',
#                 contract_data=contract_data
#             )
#
#             # **修复哈希计算，不使用 usedforsecurity 参数**
#             import hashlib
#             import sys
#             if sys.version_info >= (3, 9):
#                 pdf_hash = hashlib.md5(pdf_content, usedforsecurity=False).hexdigest()
#             else:
#                 pdf_hash = hashlib.md5(pdf_content).hexdigest()
#
#             # 返回PDF响应
#             response = HttpResponse(pdf_content, content_type='application/pdf')
#             response['Content-Disposition'] = f'attachment; filename="contract_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
#             return response
#
#         except ValueError as e:
#             # 捕获数值转换错误
#             logger.error(f"数值转换失败: {str(e)}")
#             return JsonResponse({'success': False, 'error': f'数值格式错误: {str(e)}'})
#         except Exception as e:
#             logger.error(f"PDF生成失败: {str(e)}")
#             return JsonResponse({'success': False, 'error': str(e)}, status=500)
class GenerateContractPdfView(LoginRequiredMixin, View):

    """生成PDF合同视图（完整修复版）"""

    def post(self, request):
        try:
            data = json.loads(request.body)
            current_datetime = datetime.now()
            contract_data = {
                'property_title': data.get('property_title', ''),
                'property_address': data.get('property_address', ''),
                'property_price': float(data.get('property_price', 0)),
                'property_area': data.get('property_area', ''),
                'property_type': data.get('property_type', ''),
                'buyer_name': data.get('buyer_name', ''),
                'buyer_id_card': data.get('buyer_id_card', ''),
                'buyer_phone': data.get('buyer_phone', ''),
                'buyer_address': data.get('buyer_address', ''),
                'seller_name': data.get('seller_name', ''),
                'seller_id_card': data.get('seller_id_card', ''),
                'seller_phone': data.get('seller_phone', ''),
                'seller_address': data.get('seller_address', ''),
                'tax_rate': float(data.get('tax_rate', 0)),
                'tax_amount': float(data.get('tax_amount', 0)),
                'total_price': float(data.get('total_price', 0)),
                'created_at': current_datetime.strftime('%Y-%m-%d %H:%M:%S'),  # 转换为字符串
            }

            # 获取中介信息
            agent_profile, created = RealEstateAgent.objects.get_or_create(
                user=request.user,
                defaults={
                    'license_number': f'DEFAULT_{request.user.id}',
                    'company': '默认中介公司',
                    'phone': request.user.mobile
                }
            )

            # 注册中文字体
            font_path = os.path.join(settings.BASE_DIR, 'fonts', 'simsun.ttc')
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('SimHei', font_path, subfontIndex=0))
            else:
                try:
                    pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
                except:
                    pass

            # 创建PDF文档
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []

            # 获取样式并设置中文字体
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1,
                fontName='SimHei',
                textColor=colors.black
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=16,
                fontName='SimHei',
                textColor=colors.black
            )
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName='SimHei',
                fontSize=10,
                textColor=colors.black
            )

            # 添加标题
            title = Paragraph("房屋买卖合同", title_style)
            elements.append(title)

            # 添加合同基本信息表格
            contract_info_data = [
                ["合同编号", f"HT-{current_datetime.strftime('%Y%m%d_%H%M%S')}"],
                ["签订日期", current_datetime.strftime('%Y年%m月%d日')],
            ]

            contract_info_table = Table(contract_info_data, colWidths=[2 * inch, 4 * inch])
            contract_info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, -1), 'SimHei'),
                ('FONTSIZE', (0, 0), (0, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(contract_info_table)
            elements.append(Spacer(1, 12))

            # 房产信息部分
            elements.append(Paragraph("房产信息", heading_style))

            property_data = [
                [Paragraph("房产标题", normal_style), Paragraph(contract_data['property_title'], normal_style)],
                [Paragraph("房产地址", normal_style), Paragraph(contract_data['property_address'], normal_style)],
                [Paragraph("房产价格", normal_style),
                 Paragraph(f"¥{contract_data['property_price']:,.2f}", normal_style)],
                [Paragraph("房产面积", normal_style),
                 Paragraph(f"{contract_data['property_area']} 平方米", normal_style)],
                [Paragraph("房产类型", normal_style), Paragraph(contract_data['property_type'], normal_style)],
            ]

            property_table = Table(property_data, colWidths=[1.5 * inch, 4 * inch])
            property_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 0), (-1, -1), 'SimHei'),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(property_table)
            elements.append(Spacer(1, 12))

            # 买方信息部分
            elements.append(Paragraph("买方信息", heading_style))

            buyer_data = [
                [Paragraph("姓名", normal_style), Paragraph(contract_data['buyer_name'], normal_style)],
                [Paragraph("身份证", normal_style), Paragraph(contract_data['buyer_id_card'], normal_style)],
                [Paragraph("电话", normal_style), Paragraph(contract_data['buyer_phone'], normal_style)],
                [Paragraph("地址", normal_style), Paragraph(contract_data['buyer_address'], normal_style)],
            ]

            buyer_table = Table(buyer_data, colWidths=[1.5 * inch, 4 * inch])
            buyer_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 0), (-1, -1), 'SimHei'),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(buyer_table)
            elements.append(Spacer(1, 12))

            # 卖方信息部分
            elements.append(Paragraph("卖方信息", heading_style))

            seller_data = [
                [Paragraph("姓名", normal_style), Paragraph(contract_data['seller_name'], normal_style)],
                [Paragraph("身份证", normal_style), Paragraph(contract_data['seller_id_card'], normal_style)],
                [Paragraph("电话", normal_style), Paragraph(contract_data['seller_phone'], normal_style)],
                [Paragraph("地址", normal_style), Paragraph(contract_data['seller_address'], normal_style)],
            ]

            seller_table = Table(seller_data, colWidths=[1.5 * inch, 4 * inch])
            seller_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 0), (-1, -1), 'SimHei'),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(seller_table)
            elements.append(Spacer(1, 12))

            # 价格信息部分
            elements.append(Paragraph("价格信息", heading_style))

            price_data = [
                [Paragraph("房产价格", normal_style),
                 Paragraph(f"¥{contract_data['property_price']:,.2f}", normal_style)],
                [Paragraph("税率", normal_style), Paragraph(f"{contract_data['tax_rate']}%", normal_style)],
                [Paragraph("税费", normal_style), Paragraph(f"¥{contract_data['tax_amount']:,.2f}", normal_style)],
                [Paragraph("总价", normal_style), Paragraph(f"¥{contract_data['total_price']:,.2f}", normal_style)],
            ]

            price_table = Table(price_data, colWidths=[1.5 * inch, 4 * inch])
            price_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 0), (-1, -1), 'SimHei'),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(price_table)
            elements.append(Spacer(1, 24))

            # 签名区域
            elements.append(Paragraph("签字确认", heading_style))

            signature_data = [
                [Paragraph("买方签字:", normal_style), Paragraph("_____________________", normal_style),
                 Paragraph("日期:", normal_style), Paragraph("___________", normal_style)],
                ["", "", "", ""],
                [Paragraph("卖方签字:", normal_style), Paragraph("_____________________", normal_style),
                 Paragraph("日期:", normal_style), Paragraph("___________", normal_style)],
                ["", "", "", ""],
                [Paragraph("中介签字:", normal_style), Paragraph("_____________________", normal_style),
                 Paragraph("日期:", normal_style), Paragraph("___________", normal_style)],
            ]
            signature_table = Table(signature_data, colWidths=[1.2 * inch, 2 * inch, 1 * inch, 1.5 * inch])
            signature_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0, colors.white),
                ('FONTNAME', (0, 0), (-1, -1), 'SimHei'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(signature_table)

            # 构建PDF
            doc.build(elements)

            # 获取PDF内容
            pdf_content = buffer.getvalue()
            buffer.close()

            # 创建交易记录
            from home.models import Transaction
            transaction = Transaction.objects.create(
                agent=agent_profile,
                property_title=contract_data['property_title'],
                property_address=contract_data['property_address'],
                property_price=contract_data['property_price'],
                buyer_name=contract_data['buyer_name'],
                buyer_phone=contract_data['buyer_phone'],
                seller_name=contract_data['seller_name'],
                seller_phone=contract_data['seller_phone'],
                amount=contract_data['total_price'],
                status='completed',
                contract_data=contract_data,
                user=request.user,
            )

            # 修复哈希计算
            import hashlib
            import sys
            if sys.version_info >= (3, 9):
                pdf_hash = hashlib.md5(pdf_content, usedforsecurity=False).hexdigest()
            else:
                pdf_hash = hashlib.md5(pdf_content).hexdigest()

            # 返回PDF响应
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response[
                'Content-Disposition'] = f'attachment; filename="contract_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
            return response

        except ValueError as e:
            logger.error(f"数值转换失败: {str(e)}")
            return JsonResponse({'success': False, 'error': f'数值格式错误: {str(e)}'})
        except Exception as e:
            logger.error(f"PDF生成失败: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})


class AgentPropertyManagementView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    中介管理员房屋管理页面
    """

    def test_func(self):
        # 确保只有中介用户可以访问
        return self.request.user.is_real_estate_agent or self.request.user.is_staff

    def get(self, request):
        # 获取所有房屋信息
        properties = City.objects.all().order_by('-created_at')

        # 获取搜索查询
        search_query = request.GET.get('search', '')

        if search_query:
            # 根据标题、地址、价格等字段搜索
            properties = properties.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(min_price__icontains=search_query) |
                Q(max_price__icontains=search_query) |
                Q(decoration__icontains=search_query)
            )

        # 分页处理
        page_num = request.GET.get('page_num', 1)
        page_size = request.GET.get('page_size', 10)

        paginator = Paginator(properties, per_page=page_size)
        try:
            properties = paginator.page(page_num)
        except EmptyPage:
            properties = paginator.page(1)

        total_page = paginator.num_pages

        context = {
            'properties': properties,
            'search_query': search_query,
            'page_num': page_num,
            'total_page': total_page,
            'page_size': page_size,
        }
        return render(request, 'agent_property_management.html', context)

class DeletePropertyView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    删除房屋信息视图
    """

    def test_func(self):
        # 确保只有中介用户可以删除
        return self.request.user.is_real_estate_agent or self.request.user.is_staff

    def post(self, request, property_id):
        try:
            property_obj = City.objects.get(id=property_id)
            # 使用软删除，将 is_deleted 设置为 True
            property_obj.is_deleted = True
            property_obj.save()

            messages.success(request, '房屋信息删除成功！')
        except City.DoesNotExist:
            messages.error(request, '房屋信息不存在！')

        return redirect('users:agent_property_management')
