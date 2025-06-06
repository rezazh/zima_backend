# Generated by Django 5.1.5 on 2025-06-07 10:43

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatRoom',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, verbose_name='نام اتاق')),
                ('room_type', models.CharField(choices=[('support', 'پشتیبانی'), ('general', 'عمومی'), ('private', 'خصوصی')], default='support', max_length=20, verbose_name='نوع اتاق')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('admin', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='admin_chat_rooms', to=settings.AUTH_USER_MODEL)),
                ('participants', models.ManyToManyField(blank=True, related_name='chat_rooms', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_chat_rooms', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'اتاق چت',
                'verbose_name_plural': 'اتاق\u200cهای چت',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('file', models.FileField(blank=True, null=True, upload_to='chat_files/')),
                ('file_name', models.CharField(blank=True, max_length=255, null=True)),
                ('file_size', models.IntegerField(blank=True, null=True)),
                ('file_type', models.CharField(blank=True, max_length=50, null=True)),
                ('message_type', models.CharField(choices=[('text', 'Text'), ('image', 'Image'), ('file', 'File'), ('system', 'System')], default='text', max_length=10)),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='chat.chatroom')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('chat', 'پیام چت'), ('order', 'بروزرسانی سفارش'), ('product', 'موجود شدن محصول'), ('system', 'سیستم')], max_length=30, verbose_name='نوع نوتیفیکیشن')),
                ('title', models.CharField(max_length=200, verbose_name='عنوان')),
                ('message', models.TextField(verbose_name='پیام')),
                ('data', models.JSONField(blank=True, default=dict, verbose_name='داده\u200cهای اضافی')),
                ('is_read', models.BooleanField(default=False, verbose_name='خوانده شده')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'نوتیفیکیشن',
                'verbose_name_plural': 'نوتیفیکیشن\u200cها',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='UserChatStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('online', 'آنلاین'), ('away', 'غایب'), ('busy', 'مشغول'), ('offline', 'آفلاین')], default='offline', max_length=20, verbose_name='وضعیت')),
                ('last_seen', models.DateTimeField(auto_now=True, verbose_name='آخرین بازدید')),
                ('is_staff_available', models.BooleanField(default=False, verbose_name='ادمین در دسترس')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='chat_status', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'وضعیت چت کاربر',
                'verbose_name_plural': 'وضعیت چت کاربران',
            },
        ),
        migrations.CreateModel(
            name='DeletedChat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deleted_at', models.DateTimeField(auto_now_add=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='del_messages', to='chat.chatroom')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'room')},
            },
        ),
    ]
