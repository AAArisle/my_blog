from django.db import models
from django.contrib.auth.models import User
from article.models import ArticlePost
# django-ckeditor
from ckeditor.fields import RichTextField
# django-mptt
from mptt.models import MPTTModel, TreeForeignKey

# 文章的评论
class Comment(MPTTModel):
    article = models.ForeignKey(
        ArticlePost,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    # 用django-ckeditor库自己的富文本字段RichTextField替换普通的文本字段TextField
    body = RichTextField()
    created = models.DateTimeField(auto_now_add=True)

    # 新增，mptt树形结构
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )

    # 新增，记录二级评论回复给谁, str
    reply_to = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replyers'
    )
    
    # 替换 Meta 为 MPTTMeta
    class MPTTMeta:
        order_insertion_by = ['created']

    def __str__(self):
        return self.body[:20]