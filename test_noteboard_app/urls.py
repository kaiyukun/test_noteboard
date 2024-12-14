from django.urls import path
from . import views

urlpatterns = [
    path('',views.HomeView.as_view(),name='home'),
    path('member_login',views.MemberLoginView.as_view(),name='member_login'),
    path('member_logout',views.MemberLogout,name='member_logout'),
    path('member_regist',views.MemberRegistView.as_view(), name='member_regist'),
    path('member_update/<int:pk>/', views.MemberUpdateView.as_view(), name='member_update'),
    path('member_detail/<int:pk>/', views.MemberDetailView.as_view(), name='member_detail'),
    path('member_detail/<int:pk>/update_privacy/', views.PrivacyUpdateView.as_view(), name='update_privacy'),
    path('member_detail/<int:pk>/follow/', views.FollowToggleView.as_view(), name='follow_toggle'),
    path('post_detail/<int:pk>/',views.PostDetailView.as_view(),name='post_detail'),
    path('post_create/',views.PostCreateView.as_view(),name='post_create'), 
    path('post_update/<int:pk>/',views.PostUpdateView.as_view(),name='post_update'),
    path('post_delete/<int:pk>/',views.PostDeleteView.as_view(),name='post_delete'),
    path('post/<int:pk>/like/', views.LikeToggleView.as_view(), name='like_toggle'),
    path('post/<int:pk>/comment/', views.CommentCreateView.as_view(), name='comment_create'),
    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),

]