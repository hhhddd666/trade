from django.db import models
from django.utils import timezone
from users.models import User
import uuid
# Create your models here.
class CityCategory(models.Model):
    """
    文章分类
    """
    # 分类标题
    title = models.CharField(max_length=100,blank=True)
    #创建时间
    created = models.DateTimeField(default=timezone.now)
    total_views = models.PositiveIntegerField(default=0)
    def __str__(self):
        return self.title

    class Meta:
        db_table = 'td_cities'
        verbose_name = '类别管理'
        verbose_name_plural = verbose_name


class City(models.Model):
    """
    作者、标题图、标题、分类、标签、摘要信息、文章正文、浏览量、评论量、文章的创建时间、文章的修改时间

    """
    author = models.ForeignKey(User,on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='article/%Y%m%d',blank=True)
    title = models.CharField(max_length=100,blank=True)
    sold = models.BooleanField(default=False, verbose_name='是否已售出')
    category = models.ForeignKey(
        CityCategory,
        on_delete=models.CASCADE,
        blank=True,null=True,
        related_name='city'
    )

    agent = models.ForeignKey(
        'home.RealEstateAgent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='properties',
        verbose_name='关联中介'
    )

    #标签
    description = models.TextField(max_length=20,blank=True)
    decoration = models.CharField(max_length=100,blank=True)

    #最低价
    min_price = models.CharField(max_length=100,blank=True)
    #最高价
    max_price = models.CharField(max_length=100,blank=True)
    #浏览量
    total_views = models.PositiveIntegerField(default=0)
    #评论量
    comments_count = models.PositiveIntegerField(default=0)
    # #城市的创建时间
    created_at = models.DateTimeField(default=timezone.now)
    # #城市的修改时间
    updated = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, verbose_name="是否已售出")
    def __str__(self):
        return self.title

    class Meta:
        ordering = ('-created_at',)
        db_table = 'td_purchase_request'
        verbose_name = '城市分类管理'
        verbose_name_plural = verbose_name


class Comment(models.Model):
    """
    评论
    """
    # 评论的文章
    content = models.TextField()
    article = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
    )
    # 昵称
    user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
    )
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.article.title

    class Meta:
        db_table = 'td_comment'
        verbose_name = '评论管理'
        verbose_name_plural = verbose_name

# home/models.py 中添加
class CityImage(models.Model):
    """
    城市图片 - 用于轮播图
    """
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name='images'  # 这样可以通过 city.images 访问所有图片
    )
    image = models.ImageField(upload_to='city_images/%Y%m%d', blank=True)
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'td_city_images'
        verbose_name = '城市图片管理'
        verbose_name_plural = verbose_name


class RealEstateAgent(models.Model):
    """
    房屋中介模型
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_profile')
    license_number = models.CharField(max_length=50, unique=True, verbose_name='执照号')
    company = models.CharField(max_length=100, verbose_name='所属公司')
    phone = models.CharField(max_length=11, verbose_name='联系电话')
    description = models.TextField(max_length=500, blank=True, verbose_name='个人介绍')
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True, verbose_name='是否活跃')

    class Meta:
        db_table = 'td_real_estate_agents'
        verbose_name = '房屋中介管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username} - {self.company}"




class Transaction(models.Model):
    """
    交易记录模型
    """
    BUYER = 'buyer'
    SELLER = 'seller'

    ROLE_CHOICES = [
        (BUYER, '买方'),
        (SELLER, '卖方'),
    ]

    agent = models.ForeignKey(RealEstateAgent, on_delete=models.CASCADE, verbose_name='中介')
    city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='房产')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, verbose_name='角色')
    created_at = models.DateTimeField(default=timezone.now)
    is_completed = models.BooleanField(default=False, verbose_name='是否完成')

    # 添加合同相关字段
    property_title = models.CharField(max_length=200, verbose_name='房产标题',default='')
    property_address = models.CharField(max_length=500, verbose_name='房产地址',default='')
    property_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='房产价格',default=0.00)
    buyer_name = models.CharField(max_length=100, verbose_name='买家姓名',default='')
    buyer_phone = models.CharField(max_length=20, verbose_name='买家电话',default='')
    seller_name = models.CharField(max_length=100, verbose_name='卖家姓名',default='')
    seller_phone = models.CharField(max_length=20, verbose_name='卖家电话',default='')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='交易金额',default=0.00)
    status = models.CharField(max_length=20, default='completed', verbose_name='状态')
    contract_data = models.JSONField(null=True, blank=True, verbose_name='合同数据')


    class Meta:
        db_table = 'td_transactions'
        verbose_name = '交易记录管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.property_title} - {self.buyer_name}"


# home/models.py
class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    property_article = models.ForeignKey(City, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'td_chat_messages'
        verbose_name = '聊天消息'
        verbose_name_plural = verbose_name

class ChatSession(models.Model):
    participants = models.ManyToManyField(User)
    property_article = models.ForeignKey(City, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_message = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'td_chat_sessions'
        verbose_name = '聊天会话'
        verbose_name_plural = verbose_name


class Contract(models.Model):
    contract_num = models.CharField(verbose_name="合同编号", max_length=50, unique=True, default=uuid.uuid4)
    buyer_name = models.CharField(verbose_name="买方姓名", max_length=50)
    buyer_idcard = models.CharField(verbose_name="买方身份证", max_length=18)
    seller_name = models.CharField(verbose_name="卖方姓名", max_length=50)
    seller_idcard = models.CharField(verbose_name="卖方身份证", max_length=18)
    # 关联你现有的City模型（房源）
    house = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="关联房源")
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "购房合同"
        verbose_name_plural = "购房合同"

    def __str__(self):
        return self.contract_num