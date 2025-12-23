from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('search/', views.search_users, name='search'),
    path('contacts/', views.contacts_list, name='contacts'),
    path('contacts/add/<str:username>/', views.add_contact, name='add_contact'),
    path('contacts/remove/<str:username>/', views.remove_contact, name='remove_contact'),
    path('contacts/block/<str:username>/', views.block_contact, name='block_contact'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('profile-edit/', views.profile_edit, name='profile_edit'),
    path('discover/', views.discover, name='discover'),
]
