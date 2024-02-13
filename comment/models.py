from django.db import models
from django.contrib.auth.models import User
from article.models import ArticlePost
# django-ckeditor
from ckeditor.fields import RichTextField

# 文章的评论
class Comment(models.Model):
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

    class Meta:
        ordering = ('created',)

    def __str__(self):
        return self.body[:20]