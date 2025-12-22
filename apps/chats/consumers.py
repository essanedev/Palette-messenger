import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Chat, Message, MessageReadStatus


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'
        self.user = self.scope['user']

        print(f"WebSocket подключен: chat_id={self.chat_id}, user={self.user}")

        if not self.user.is_authenticated:
            print(f"юзер не авторизован")
            await self.close()
            return

        has_access = await self.check_chat_access()
        if not has_access:
            print(f"юзер {self.user.username} нет доступа к чату {self.chat_id}")
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        print(f"WebSocket подключен: юзер {self.user.username} присоединился {self.chat_id}")

        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to chat',
            'chat_id': self.chat_id
        }))

    async def disconnect(self, close_code):
        print(f"WebSocket отключен: юзер {self.user.username} покинул чат {self.chat_id}, код: {close_code}")

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            print(f"получено сообщение: тип={message_type}, дата={data}")

            if message_type == 'chat_message':
                content = data.get('message')
                if not content or not content.strip():
                    print(f"пустой")
                    return

                message = await self.save_message(content)
                print(f"сообщение сохранено: id={message.id}, content={message.content[:50]}")

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': {
                            'id': message.id,
                            'content': message.content,
                            'sender': message.sender.username,
                            'sender_avatar': message.sender.avatar.url if message.sender.avatar else None,
                            'created_at': message.created_at.isoformat(),
                            'message_type': message.message_type,
                            'file_url': message.file.url if message.file else None,
                        }
                    }
                )
                print(f"сообщение отправлено в группу {self.room_group_name}")

            elif message_type == 'typing':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_indicator',
                        'user': self.user.username,
                        'is_typing': data.get('is_typing', False)
                    }
                )

        except Exception as e:
            print(f"ошибка при получении: {str(e)}")
            import traceback
            traceback.print_exc()
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def chat_message(self, event):
        print(f"Отправлено сообщение: {event['message']['id']}")
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))

    async def typing_indicator(self, event):
        if event['user'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user': event['user'],
                'is_typing': event['is_typing']
            }))

    @database_sync_to_async
    def check_chat_access(self):
        try:
            chat = Chat.objects.get(id=self.chat_id)
            has_access = chat.members.filter(id=self.user.id).exists()
            print(f"проверка доступа: чат={self.chat_id}, юзер={self.user.username}, доступ={has_access}")
            return has_access
        except Chat.DoesNotExist:
            print(f"чата {self.chat_id} нет")
            return False

    @database_sync_to_async
    def save_message(self, content):
        chat = Chat.objects.get(id=self.chat_id)
        message = Message.objects.create(
            chat=chat,
            sender=self.user,
            content=content,
            message_type='text'
        )
        return message