from django.urls import path

from . import views
from home.views import IndexView,DetailView

urlpatterns = [
    #首页的路由
    path('', IndexView.as_view(),name='index'),

    path('detail/<int:id>/', DetailView.as_view(), name='detail'),

]
