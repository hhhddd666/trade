from django.core.paginator import Paginator,EmptyPage
from django.urls import reverse
from django.contrib.admin.templatetags.admin_list import pagination
from django.http import HttpResponseNotFound
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.db.models import Q  # 添加这个导入
from home.models import CityCategory, City ,Comment
from users.models import User


# Create your views here.
class IndexView(View):
    """
        提供首页跳转
    """
    # 1、获取所有分类信息
    def get(self, request):
        categories = CityCategory.objects.all()
        cat_id = request.GET.get('cat_id', 1)
        search_query = request.GET.get('search', '')  # 获取搜索查询
        try:
            category = CityCategory.objects.get(id=cat_id)
        except CityCategory.DoesNotExist:
            return HttpResponseNotFound('没有此分类')
        #获取分页参数
        page_num = request.GET.get('page_num',1)
        page_size = request.GET.get('page_size',10)
        #根据分页信息查询文章数据

        # 如果有搜索查询，则过滤数据
        if search_query:
            purchase_requests = City.objects.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(decoration__icontains=search_query) |
                Q(min_price__icontains=search_query) |
                Q(max_price__icontains=search_query),
                is_deleted=False
            ).order_by('-created_at')  # 添加排序
        else:
            purchase_requests = City.objects.filter(category=category, sold=False, is_deleted=False).order_by('-created_at')  # 添加排序
            # 检查搜索结果数量，如果只有一条，直接跳转到详情页
        if search_query:
            search_count = purchase_requests.count()
            if search_count == 1:
                single_article = purchase_requests.first()
                return redirect('home:detail', id=single_article.id)
        #创建分页器
        paginator = Paginator(purchase_requests, per_page=page_size)
        #进行分页处理
        try:
            purchase_requests = paginator.page(page_num)
        except EmptyPage :
            return HttpResponseNotFound('没有此页')
        #获取总页数
        total_page = paginator.num_pages
        context = {
            'categories': categories,
            'category': category,
            'purchase_requests': purchase_requests,
            'page_size': page_size,
            'total_page': total_page,
            'page_num': page_num,
            'search_query': search_query,  # 将搜索查询添加到上下文中
        }
        return render(request, 'index.html',context=context)
# class IndexView(View):
#     """
#         提供首页跳转
#     """
#     # 1、获取所有分类信息
#     def get(self, request):
#         categories = CityCategory.objects.all()
#         cat_id = request.GET.get('cat_id', 1)
#         try:
#             category = CityCategory.objects.get(id=cat_id)
#         except CityCategory.DoesNotExist:
#             return HttpResponseNotFound('没有此分类')
#         #获取分页参数
#         page_num = request.GET.get('page_num',1)
#         page_size = request.GET.get('page_size',10)
#         #根据分页信息查询文章数据
#         purchase_requests = City.objects.filter(category=category)
#         #创建分页器
#         paginator = Paginator(purchase_requests, per_page=page_size)
#         #进行分页处理
#         try:
#             page_purchase_requests = paginator.page(page_num)
#         except EmptyPage :
#             return HttpResponseNotFound('没有此页')
#         #获取总页数
#         total_page = paginator.num_pages
#         context = {
#             'categories': categories,
#             'category': category,
#             'purchase_requests': page_purchase_requests,
#             'page_size': page_size,
#             'total_page': total_page,
#             'page_num': page_num,
#         }
#         return render(request, 'index.html',context=context)

# class IndexView(View):
#     """
#         提供首页跳转
#     """
#     # 1、获取所有分类信息
#     def get(self, request):
#         categories = CityCategory.objects.all()
#         cat_id = request.GET.get('cat_id', 1)
#         try:
#             category = CityCategory.objects.get(id=cat_id)
#         except CityCategory.DoesNotExist:
#             return HttpResponseNotFound('没有此分类')
#         #获取分页参数
#         page_num = request.GET.get('page_num',1)
#         page_size = request.GET.get('page_size',10)
#         #根据分页信息查询文章数据
#         purchase_requests = City.objects.filter(category=category)
#         #创建分页器
#         paginator = Paginator(purchase_requests, per_page=page_size)
#         #进行分页处理
#         try:
#             purchase_requests = paginator.page(page_num)
#         except EmptyPage :
#             return HttpResponseNotFound('没有此页')
#         #获取总页数
#         total_page = paginator.num_pages
#         context = {
#             'categories': categories,
#             'category': category,
#             'purchase_requests': purchase_requests,
#             'page_size': page_size,
#             'total_page': total_page,
#             'page_num': page_num,
#         }
#         return render(request, 'index.html',context=context)

# class IndexsView(View):
#     """
#         提供首页跳转
#     """
#     # 1、获取所有分类信息
#     def get(self, request):
#         categoriess = CityCategory.objects.all()
#         cats_id = request.GET.get('cat_id', 1)
#         try:
#             categorys = CityCategory.objects.get(id=cats_id)
#         except CityCategory.DoesNotExist:
#             return HttpResponseNotFound('没有此分类')
#         #获取分页参数
#         pages_num = request.GET.get('page_num',1)
#         pages_size = request.GET.get('page_size',10)
#         #根据分页信息查询文章数据
#         purchase_requests = City.objects.filter(category=categorys)
#         #创建分页器
#         paginators = Paginator(purchase_requests, per_page=pages_size)
#         #进行分页处理
#         try:
#             purchase_requests = paginators.page(pages_num)
#         except EmptyPage :
#             return HttpResponseNotFound('没有此页')
#         #获取总页数
#         totals_page = paginators.num_pages
#         context = {
#             'categoriess': categoriess,
#             'categorys': categorys,
#             'purchases_requests': purchase_requests,
#             'pages_size': pages_size,
#             'totals_page': totals_page,
#             'pages_num': pages_num,
#         }
#         return render(request, 'center.html',context=context)

class DetailView(View):
    def get(self,request, id=None):
        if id is None:
            id = request.GET.get('id')

        if id is None:
            return render(request, '404.html')
        try:
            article = City.objects.get(id=id)
        except City.DoesNotExist:
            return render(request,'404.html')
        else:
            article.total_views += 1
            article.save()

        categories = CityCategory.objects.all()

        # 获取该文章的所有图片（用于轮播图）
        images = article.images.all()  # 通过 related_name 访问

        #查询浏览量前十的文章数据
        hot_articles = City.objects.order_by('-total_views')[:10]

        page_size = request.GET.get('page_size',10)
        page_num = request.GET.get('page_num',1)
        comments = Comment.objects.filter(article=article).order_by('-created')
        total_count = comments.count()
        paginator = Paginator(comments,page_size)
        try:
            page_comments = paginator.page(page_num)
        except EmptyPage:
            return HttpResponseNotFound('没有此页')

        total_page = paginator.num_pages


        context = {
            'categories': categories,
            'category': article.category,
            'article': article,
            'images':images,
            'hot_articles': hot_articles,
            'comments': page_comments,
            'total_page': total_page,
            'page_num': page_num,
            'total_count': total_count,
            'page_size': page_size,
        }
        return render(request,'detail.html',context=context)

    def post(self,request):
        user = request.user
        if user and user.is_authenticated:
            id = request.POST.get('id')
            content = request.POST.get('content')
            try:
                article = City.objects.get(id=id)
            except City.DoesNotExist:
                return render(request,'404.html')
            Comment.objects.create(
                content=content,
                article=article,
                user=user
            )
            article.comments_count += 1
            article.save()
            path=reverse('home:detail',kwargs={'id': article.id})
            return redirect(path)

        else:
            return redirect(reverse('users:login'))


