from django.urls import path
from . import views

app_name = 'chats'

urlpatterns = [
    path('', views.chats_list, name='list'),
    path('<int:chat_id>/', views.chat_detail, name='detail'),
    path('create/private/<str:username>/', views.create_private_chat, name='create_private'),
    path('groups/create/', views.create_group, name='create_group'),
    path('search/groups/', views.search_groups, name='search_groups'),
    path('groups/<int:group_id>/join/', views.join_group, name='join_group'),
    path('<int:chat_id>/add-member/', views.add_member_to_group, name='add_member'),
    path('<int:chat_id>/upload-file/', views.upload_file, name='upload_file'),
    path('<int:chat_id>/upload-voice/', views.upload_voice, name='upload_voice'),
    path('discover/', views.discover, name='discover'),
]