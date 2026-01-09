from django.urls import path

from . import views
from users.views import *
from home.views import IndexView

"""
        参数1：路由
        参数2：视图函数
        参数3：路由名称，方便后续通过reverse获得路由
        as_view（）：方法将类转换为视图函数
        根据用户请求类型好，返回对应的方法
    """
urlpatterns = [

    path('register/', RegisterView.as_view(),name='register'),
    #图形验证码路由
    path('imagecode/',ImageCodeView.as_view(),name='imagecode'),
    #发送短信验证码
    path('smscode/',SmsCodeView.as_view(),name='smscode'),
    #登录路由
    path('login/',LoginView.as_view(),name='login'),
    #退出登录
    path('logout/',LogoutView.as_view(),name='logout'),
    #忘记密码
    path('forgetpassword/',ForgetPasswordView.as_view(),name='forgetpassword'),
    #个人中心
    path('writeblog/',WriteBlogView.as_view(),name='writeblog'),
    path('center/',UserCenterView.as_view(),name='center'),
    path('indexview/',IndexView.as_view(),name='indexview'),

    path('delete_purchase/', views.DeletePurchaseRequestView.as_view(), name='delete_purchase'),

    path('delete-article/', DeleteCityView.as_view(), name='delete_article'),

    # 中介管理URL
    path('agents/admin/', AgentManagementView.as_view(), name='agent_management'),
    path('agents/admin/<int:agent_id>/', AgentDetailView.as_view(), name='agent_detail'),
    path('admin/agents/<int:agent_id>/', AgentDetailView.as_view(), name='agent_detail'),

    # 中介个人中心URL
    path('agent/center/', views.AgentCenterView.as_view(), name='agent_center'),
    path('agent/contracts/', views.AgentContractView.as_view(), name='agent_contracts'),
    path('agent/transactions/', views.AgentTransactionView.as_view(), name='agent_transactions'),

    path('chat/messages/', ChatView.as_view(), name='chat_messages'),
    path('chat/send/', SendMessageView.as_view(), name='send_message'),
    # 确保这行存在
    path('agent/generate-contract-pdf/', views.GenerateContractPdfView.as_view(), name='generate_contract_pdf'),
    # 在 urlpatterns 列表中添加
    path('agent/property-management/', views.AgentPropertyManagementView.as_view(), name='agent_property_management'),
    path('agent/delete-property/<int:property_id>/', views.DeletePropertyView.as_view(), name='delete_property'),

]
