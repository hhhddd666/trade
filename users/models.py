from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
#用户信息，用户集成自AbstractUser
class User(AbstractUser):
    #电话号码字段
    #unique唯一性字段，black表示是否为空，black=false表示必须填写
    mobile = models.CharField(max_length=11, unique=True,blank = False)
    description = models.TextField(max_length=20, blank=True)

    #头像字段
    avatar = models.ImageField(blank=True)

    # 中介角色字段
    is_real_estate_agent = models.BooleanField(default=False, verbose_name='是否为房屋中介')
    agent_license = models.CharField(max_length=50, blank=True, verbose_name='中介执照号')
    agent_company = models.CharField(max_length=100, blank=True, verbose_name='所属公司')
    agent_phone = models.CharField(max_length=11, blank=True, verbose_name='中介联系电话')
    # user_desc = models.TextField(max_length=500,blank=True)

    #认证方式修改为手机号码认证
    #修改认证字段
    USERNAME_FIELD = 'mobile'

    #创建超级管理员的认证字段
    REQUIRED_FIELDS = ['username','email']

    #内部类，用于给模型定义源数据
    class Meta:
        db_table = 'td_users'#修改数据库默认的表名
        verbose_name = '用户管理'#admin后台管理显示名称
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.mobile



    # 49.20min