from django.urls import path
from . import views

app_name = 'chats'

urlpatterns = [
    path('', views.chats_list, name='list'),
    path('<int:chat_id>/', views.chat_detail, name='detail'),
    path('create/private/<str:username>/', views.create_private_chat, name='create_private'),
    path('create/group/', views.create_group_chat, name='create_group'),
    path('search/groups/', views.search_groups, name='search_groups'),
    path('join/<int:chat_id>/', views.join_group, name='join_group'),
    path('<int:chat_id>/add-member/', views.add_member_to_group, name='add_member'),
]