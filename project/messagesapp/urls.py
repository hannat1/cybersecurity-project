from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'messagesapp'
urlpatterns = [
    path('', views.index, name='index'),
    path('<int:message_id>/', views.detail, name='detail'),
    path('new_message/', views.new_message, name='new_message'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),
    path('search/', views.search_messages, name='search'),
]