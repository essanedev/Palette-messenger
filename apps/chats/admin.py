from django.contrib import admin
from .models import Chat, ChatMembership, Message, MessageReadStatus

# Register your models here.

class ChatMembershipInline(admin.TabularInline):
    model = ChatMembership
    extra = 1

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'chat_type', 'created_at', 'updated_at']
    list_filter = ['chat_type', 'created_at']
    search_fields = ['name', 'description']
    inlines = [ChatMembershipInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'chat', 'message_type', 'content', 'created_at', 'is_edited']
    list_filter = ['message_type', 'is_edited', 'is_deleted', 'created_at']
    search_fields = ['content', 'sender__username']
    raw_id_fields = ['chat', 'sender', 'reply_to']


@admin.register(MessageReadStatus)
class MessageReadStatusAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'read_at']
    list_filter = ['read_at']
    search_fields = ['user__username']