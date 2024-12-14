from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Member, Comment, Post, Category, Tag
from transformers import pipeline
import logging

logger = logging.getLogger(__name__)

# zero-shot-classificationのパイプラインを作成
classifier = pipeline("zero-shot-classification")


class MemberForm(UserCreationForm):
    class Meta:
        model = Member
        fields = ['username', 'email', 'password1', 'password2', 'birth_date', 'about_me', 'member_image']
        widgets = {
            'member_image': forms.ClearableFileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*',  # 画像ファイルのみを選択できるようにする
            }),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'about_me': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class MemberUpdateForm(UserChangeForm):
    password1 = forms.CharField(
        label="新しいパスワード",
        widget=forms.PasswordInput,
        required=False,
    )
    password2 = forms.CharField(
        label="新しいパスワード（確認用）",
        widget=forms.PasswordInput,
        required=False,
        help_text="確認のため、もう一度新しいパスワードを入力してください。"
    )

    class Meta:
        model = Member
        fields = ['username', 'email', 'birth_date', 'about_me', 'member_image']
        widgets = {
            'member_image': forms.ClearableFileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*',  # 画像ファイルのみを選択できるようにする
            }),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'about_me': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class PostForm(forms.ModelForm):
    new_tags = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '新しいタグを追加'}),
        initial=''
    )

    class Meta:
        model = Post
        fields = ['title', 'content', 'tags', 'category']

    def clean_new_tags(self):
        # 新しいタグが入力された場合、保存できる形式にする
        new_tags = self.cleaned_data['new_tags']
        if new_tags:
            # カンマ区切りでタグを分割
            return [tag.strip() for tag in new_tags.split(',')]
        return []

    def save(self, commit=True):
        post = super().save(commit=False)
        post.save()

        tags = self.cleaned_data.get('tags')
        for tag_name in tags:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            post.tags.add(tag)

        # 新しいタグがあれば保存して、投稿に関連付け
        new_tags = self.cleaned_data.get('new_tags')
        for tag_name in new_tags:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            post.tags.add(tag)

        # 投稿内容に基づき、zero-shot-classificationでタグを推定
        post_content = post.content
        candidate_labels = Tag.objects.all()
        result = classifier(post_content, candidate_labels=candidate_labels)
        
        # 最も関連性の高いタグを取得
        best_tag = result['labels'][0]
        tag, created = Tag.objects.get_or_create(name=best_tag)
        post.tags.add(tag)

        return post