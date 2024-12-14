from django.db import models

from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from ckeditor.fields import RichTextField

class Member(AbstractUser):
    # デフォルトユーザーテーブルに追加したいフィールド
    birth_date = models.DateField(null=True, blank=True)
    about_me = models.TextField(max_length=500, blank=True)
    member_image = models.ImageField(upload_to="profile_pics",blank=True)
    # フォロー機能のための多対多フィールド
    followers = models.ManyToManyField('self', symmetrical=False, related_name='following')
    only_followers_flg = models.BooleanField(default=False)

    def __str__(self):
            return self.username
    
class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=50)
    content = RichTextField()
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return self.title
    
class Like(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('member', 'post')

class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.user} on {self.post}'
    
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('follow', 'Follow'),
        ('comment', 'Comment'),
    )

    sender = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='sent_notifications')
    recipient = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.sender} to {self.recipient}: {self.notification_type}'
    
