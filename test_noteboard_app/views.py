from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy, reverse
from . import forms
from . import models
from django.http import HttpResponseRedirect
from django.contrib.auth.views import LoginView
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
import logging

from django.core.mail import send_mail

logger = logging.getLogger(__name__)

#ログイン
class MemberLoginView(LoginView):
    template_name = 'test_noteboard_app_HTML/member_login.html'
    
#ログアウト
@login_required
def MemberLogout(request):
    logout(request)
    # ログイン画面遷移
    return HttpResponseRedirect(reverse('member_login'))

#会員登録
class MemberRegistView(CreateView):
    model = models.Member
    form_class = forms.MemberForm
    template_name = 'test_noteboard_app_HTML/member_regist.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        member = form.save(commit=False)
        member.set_password(form.cleaned_data['password1'])
        member.save()
        self.object = member
        login(self.request, member)

        send_mail(
            '会員登録ありがとうございます。',  # 件名
            'この度は会員登録していただきありがとうございます。',  # メッセージ
            'mbiclife0@gmail.com',  # 送信元のメールアドレス
            [member.email],  # 送信先のメールアドレスのリスト
            fail_silently=False,
        )
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))
    
#会員更新
class MemberUpdateView(LoginRequiredMixin, UpdateView):
    model = models.Member
    form_class = forms.MemberUpdateForm
    template_name = 'test_noteboard_app_HTML/member_regist.html'
    def get_success_url(self):
        return reverse('member_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        # ユーザー情報を保存
        member = form.save(commit=False)

        # パスワードが更新された場合にのみセット
        if form.cleaned_data.get('password1'):
            member.set_password(form.cleaned_data['password1'])

        member.save()
        self.object = member

        # ユーザーがパスワードを変更した場合、再度ログイン処理
        if form.cleaned_data.get('password1'):
            login(self.request, member)

        return super().form_valid(form)

    def form_invalid(self, form):
        # フォームのエラーをログに出力
        logger.error("Form submission failed with errors: %s", form.errors)
        return self.render_to_response(self.get_context_data(form=form))
    
class MemberDetailView(LoginRequiredMixin, DetailView):
    model = models.Member
    template_name = "test_noteboard_app_HTML/member_detail.html"
    context_object_name = "member"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ログイン中のメンバーの投稿
        context['posts'] = models.Post.objects.filter(member=self.object)
        context['is_following'] = self.request.user in self.object.followers.all()
        return context

class PrivacyUpdateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        member = get_object_or_404(models.Member, id=kwargs['pk'])

        # 現在のフラグの値をトグル
        member.only_followers_flg = not member.only_followers_flg
        member.save()

        return redirect('member_detail', pk=member.id)

# フォロー処理  
class FollowToggleView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        target_member = get_object_or_404(models.Member, pk=kwargs['pk'])
        current_member = request.user

        if target_member != current_member:
            if current_member in target_member.followers.all():
                # フォローを解除
                target_member.followers.remove(current_member)
            else:
                # フォローする
                target_member.followers.add(current_member)

                # 通知の作成
                models.Notification.objects.create(
                    sender=current_member,
                    recipient=target_member,
                    notification_type='follow'
                )

        return redirect('member_detail', pk=target_member.pk)
    
#ホーム
class HomeView(LoginRequiredMixin, ListView):
    model = models.Post
    template_name = 'test_noteboard_app_HTML/home.html'
    context_object_name = 'post_list'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['username'] = self.request.user.username
        context['categories'] = models.Category.objects.all
        context['unread_notifications_count'] = models.Notification.objects.filter(recipient=self.request.user, is_read=False).count()

        # 投稿検索結果表示時は最新記事および人気記事一覧は表示させない
        query = self.request.GET.get('query')
        context['is_search'] = bool(query)
        if not query:
            context['latest_posts'] = models.Post.objects.order_by('-created_at')[:5]
            context['popular_posts'] = models.Post.objects.annotate(like_count=Count('like')).order_by('-like_count')[:5]

        return context
    
    # 表示する一覧データの絞り込み
    def get_queryset(self, **kwargs):
        queryset = super().get_queryset(**kwargs)
        member = self.request.user

        # 鍵垢の投稿は表示させないようにする処理
        queryset = queryset.filter(
            # 限定公開ではない投稿は表示する
            Q(member__only_followers_flg=False) |
            # ログイン中のメンバーがフォローしているメンバーの投稿は表示する
            Q(member__followers=member) |
            # 投稿者本人の投稿は表示する
            Q(member=member)
        )

        # カテゴリフィルターの追加
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category__id=category_id)

        query = self.request.GET.get('query')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(member__username__icontains=query)
            )

        return queryset
    
# 投稿詳細
class PostDetailView(LoginRequiredMixin, DetailView):
    #Companyテーブル連携
    model = models.Post
    #レコード情報をテンプレートに渡すオブジェクト
    context_object_name = "post_detail"
    #テンプレートファイル連携
    template_name = "test_noteboard_app_HTML/post_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_liked = False
        post = self.get_object()
        if self.request.user.is_authenticated:
            is_liked = models.Like.objects.filter(member=self.request.user, post=post).exists()
        context['is_liked'] = is_liked

        # コメント一覧を取得してコンテキストに追加
        context['comments'] = post.comments.all()

        # コメント投稿用のフォームをコンテキストに追加
        context['comment_form'] = forms.CommentForm()

        return context
    
#投稿登録画面
class PostCreateView(LoginRequiredMixin, CreateView):
    model = models.Post
    form_class = forms.PostForm
    #テンプレートファイル連携
    template_name = "test_noteboard_app_HTML/post_regist.html"
    #更新後のリダイレクト先
    def get_success_url(self):
        return reverse('post_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.member = self.request.user
        return super().form_valid(form)
    
#投稿更新画面
class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = models.Post
    # ↓こちらにcategoryを追加する
    fields = ("title","content","published","category")
    #テンプレートファイル連携
    template_name = "test_noteboard_app_HTML/post_regist.html"
    #更新後のリダイレクト先
    def get_success_url(self):
        return reverse('post_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.member = self.request.user
        return super().form_valid(form)
    
#削除画面
class PostDeleteView(DeleteView):
    model = models.Post
    #削除後のリダイレクト先
    success_url = reverse_lazy("home")

# いいね機能
class LikeToggleView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        post = get_object_or_404(models.Post, id=kwargs['pk'])
        like, created = models.Like.objects.get_or_create(member=request.user, post=post)
        
        if created:
            # 通知を作成
            if post.member != request.user:  # 自分の投稿には通知しない
                # 通知の作成
                models.Notification.objects.create(
                    sender=request.user,
                    recipient=post.member,
                    notification_type='like',
                    post=post
                )
        else:
            like.delete()
        
        return redirect('post_detail', pk=post.id)
    
# コメント登録
class CommentCreateView(CreateView):
    model = models.Comment
    form_class = forms.CommentForm

    def form_valid(self, form):
        form.instance.member = self.request.user
        form.instance.post = get_object_or_404(models.Post, id=self.kwargs['pk'])
        form.save()

        # 通知を作成
        if form.instance.post.member != self.request.user:  # 自分の投稿には通知しない
            models.Notification.objects.create(
                sender=self.request.user,
                recipient=form.instance.post.member,
                notification_type='comment',
                post=form.instance.post,
                comment=form.instance
            )

        return redirect('post_detail', pk=self.kwargs['pk'])

# 通知一覧
class NotificationListView(LoginRequiredMixin, ListView):
    model = models.Notification
    template_name = 'test_noteboard_app_HTML/notification_list.html'
    context_object_name = 'notifications'

    def get_queryset(self):
        return models.Notification.objects.filter(recipient=self.request.user).order_by('-created_at')
    
    def get(self, request, *args, **kwargs):
        # 親クラスの get メソッドを呼び出す前に未読通知を既読に更新
        notifications = self.get_queryset()
        unread_notifications = notifications.filter(is_read=False)
        unread_notifications.update(is_read=True)
        
        # 親クラスの get メソッドを呼び出して通知のリストを取得
        return super().get(request, *args, **kwargs)