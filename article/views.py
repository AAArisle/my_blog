# 导入 HttpResponse 模块
from django.http import HttpResponse

from django.shortcuts import render

# 导入数据模型ArticlePost
from .models import ArticlePost

# 引入markdown模块
import markdown

from django.contrib.auth.decorators import login_required

# 引入分页模块
from django.core.paginator import Paginator

# 引入 Q 对象
from django.db.models import Q

# 评论
from comment.models import Comment

# 引入评论表单
from comment.forms import CommentForm

# 文章列表
def article_list(request):
    # 从 url 中提取查询参数
    search = request.GET.get('search')
    order = request.GET.get('order')
    column = request.GET.get('column')
    tag = request.GET.get('tag')

    # 初始化查询集
    article_list = ArticlePost.objects.all()
    
    # 搜索查询集
    if search:
        article_list = ArticlePost.objects.filter(
            Q(title__icontains=search) |
            Q(body__icontains=search)
        )
    else:
        # 将 search 参数重置为空
        search = ''

     # 栏目查询集
    if column is not None and column.isdigit():
        article_list = article_list.filter(column=column)

    # 标签查询集
    if tag and tag != 'None':
        article_list = article_list.filter(tags__name__in=[tag])

    # 根据GET请求中查询条件返回不同排序的对象数组
    # 按照浏览量排序显示
    if order == 'total_views':
        # 取出所有博客文章
        article_list = article_list.order_by('-total_views')

    # 按照默认（时间）排序显示
    else:
        order = 'normal'

    # 每页显示9篇文章
    paginator = Paginator(article_list, 9)

    # 获取url中的页码
    page = request.GET.get('page')
    # 将导航对象相应的页码内容返回给 articles
    articles = paginator.get_page(page)
    
    # 需要传递给模板（templates）的对象
    context = { 
        'articles': articles,
        'order': order,
        'search': search,
        'column': column,
        'tag': tag,
        }
    # render函数：载入模板，并返回context对象
    return render(request, 'article/list.html', context)

# 文章详情
def article_detail(request, id):
    # 取出相应的文章
    article = ArticlePost.objects.get(id=id)

    # 浏览量 +1
    article.total_views += 1
    article.save(update_fields=['total_views'])

    # 将markdown语法渲染成html样式
    # article.body = markdown.markdown(article.body,
    md = markdown.Markdown(
        extensions=[
        # 包含 缩写、表格等常用扩展
        'markdown.extensions.extra',
        # 语法高亮扩展
        'markdown.extensions.codehilite',
        # 目录扩展
        'markdown.extensions.toc',
        ])
    article.body = md.convert(article.body)

    # 取出文章评论
    comments = Comment.objects.filter(article=id)
    # filter()可以取出多个满足条件的对象，而get()只能取出1个

    # 引入评论表单
    comment_form = CommentForm()

    # 需要传递给模板的对象
    context = { 
        'article': article, 
        'toc': md.toc, 
        'comment_form': comment_form,
        'comments': comments 
    }
    # 载入模板，并返回context对象
    return render(request, 'article/detail.html', context)

# 引入redirect重定向模块
from django.shortcuts import render, redirect
# 引入HttpResponse
from django.http import HttpResponse
# 引入刚才定义的ArticlePostForm表单类
from .forms import ArticlePostForm
# 引入User模型
from django.contrib.auth.models import User
# 引入栏目Model
from .models import ArticleColumn

# 提醒用户登录
@login_required(login_url='/userprofile/login/')
# 写文章的视图
def article_create(request):
    # 判断用户是否提交数据
    if request.method == "POST":
        # 将提交的数据赋值到表单实例中
        article_post_form = ArticlePostForm(request.POST, request.FILES)
        # 判断提交的数据是否满足模型的要求
        if article_post_form.is_valid():
            # 保存数据，但暂时不提交到数据库中
            new_article = article_post_form.save(commit=False)

            # 指定数据库中 id=1 的用户为作者
            # new_article.author = User.objects.get(id=1)
            # 指定目前登录的用户为作者
            new_article.author = User.objects.get(id=request.user.id)

            # 栏目
            if request.POST['column'] != 'none':
                new_article.column = ArticleColumn.objects.get(id=request.POST['column'])

            # 将新文章保存到数据库中
            new_article.save()

            # 保存 tags 的多对多关系
            article_post_form.save_m2m()

            # 完成后返回到文章列表
            return redirect("article:article_list")
        # 如果数据不合法，返回错误信息
        else:
            return HttpResponse("表单内容有误，请重新填写。")
    # 如果用户请求获取数据
    else:
        # 创建表单类实例
        article_post_form = ArticlePostForm()
        # 栏目
        columns = ArticleColumn.objects.all()
        # 赋值上下文
        context = {
            'article_post_form': article_post_form, 
            'columns': columns 
        }
        # 返回模板
        return render(request, 'article/create.html', context)
    
# 提醒用户登录
@login_required(login_url='/userprofile/login/')
# 删文章
def article_delete(request, id):
    # 根据 id 获取需要删除的文章
    article = ArticlePost.objects.get(id=id)

    # 过滤非作者的用户
    if article.author != request.user:
        return HttpResponse("抱歉，你无权删除这篇文章。")
    
    # 调用.delete()方法删除文章
    article.delete()
    # 完成删除后返回文章列表
    return redirect("article:article_list")

# 提醒用户登录
@login_required(login_url='/userprofile/login/')
# 更新文章
def article_update(request, id):
    """
    更新文章的视图函数
    通过POST方法提交表单，更新titile、body字段
    GET方法进入初始表单页面
    id： 文章的 id
    """

    # 获取需要修改的具体文章对象
    article = ArticlePost.objects.get(id=id)

    # 过滤非作者的用户
    if article.author != request.user:
        return HttpResponse("抱歉，你无权修改这篇文章。")
    
    # 判断用户是否为 POST 提交表单数据
    if request.method == "POST":
        # 将提交的数据赋值到表单实例中
        article_post_form = ArticlePostForm(data=request.POST)
        # 判断提交的数据是否满足模型的要求
        if article_post_form.is_valid():
            # 保存新写入的 title、body 数据并保存
            article.title = request.POST['title']
            article.body = request.POST['body']

            # 保存文章栏目
            if request.POST['column'] != 'none':
                article.column = ArticleColumn.objects.get(id=request.POST['column'])
            else:
                article.column = None
            
            # 保存 tags，删掉空tag
            tag = request.POST.get('tags').split(',')
            tag = list(filter(None, tag))
            article.tags.set(tag, clear=True)

            # 文章的标题图
            if request.FILES.get('avatar'):
                article.avatar = request.FILES.get('avatar')

            article.save()

            # 完成后返回到修改后的文章中。需传入文章的 id 值
            return redirect("article:article_detail", id=id)
        # 如果数据不合法，返回错误信息
        else:
            return HttpResponse("表单内容有误，请重新填写。")

    # 如果用户 GET 请求获取数据
    else:
        # 创建表单类实例
        article_post_form = ArticlePostForm()
        # 栏目
        columns = ArticleColumn.objects.all()
        # 赋值上下文，将 article 文章对象也传递进去，以便提取旧的内容
        context = { 
            'article': article, 
            'article_post_form': article_post_form,
            'columns': columns,
            'tags': ','.join([x for x in article.tags.names()]),
        }
        # 将响应返回到模板中
        return render(request, 'article/update.html', context)
    
# 点赞数+1
def increase_Likes(request,id):
    article = ArticlePost.objects.get(id=id)
    article.likes += 1
    article.save()
    return redirect("article:article_detail", id=id)
