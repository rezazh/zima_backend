from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q, Count
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_POST

from .models import ChatRoom, ChatMessage, UserChatStatus, Notification, DeletedChat
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
User = get_user_model()


@login_required
def chat_list(request):
    user_chats = ChatRoom.objects.filter(
        user=request.user,
        is_active=True,
    ).exclude(
        id__in=DeletedChat.objects.filter(user=request.user).values('room_id')  # حذف چت‌های حذف شده توسط کاربر
    ).order_by('-updated_at')

    for chat in user_chats:
        chat.unread_count = ChatMessage.objects.filter(
            room=chat,
            is_read=False
        ).exclude(sender=request.user).count()

    context = {
        'user_chats': user_chats,
    }

    return render(request, 'chat/chat_list.html', context)


@login_required
def chat_room(request, room_id):
    try:
        room = ChatRoom.objects.get(id=room_id)

        # بررسی دسترسی کاربر
        if not request.user.is_staff and request.user != room.user:
            from django.contrib import messages as django_messages
            django_messages.error(request, 'شما اجازه دسترسی به این چت را ندارید.')
            return redirect('chat:chat_list')

        is_deleted_by_user = DeletedChat.objects.filter(room=room, user=room.user).exists()

        if request.user.is_staff:
            unread_messages = room.messages.filter(is_read=False, sender=room.user)
        else:
            unread_messages = room.messages.filter(is_read=False).exclude(sender=request.user)

        channel_layer = None
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
        except Exception as e:
            print(f"Error getting channel layer: {e}")

        for message in unread_messages:
            message.is_read = True
            message.save()

            if channel_layer:
                try:
                    async_to_sync(channel_layer.group_send)(
                        f'chat_{room.id}',
                        {
                            'type': 'message_read',
                            'message_id': str(message.id),
                            'read_by_user_id': request.user.id
                        }
                    )
                    print(f"Sent message_read event for message {message.id}")
                except Exception as e:
                    print(f"Error sending to channel: {e}")

        chat_messages = room.messages.all().order_by('created_at')

        online_users = UserChatStatus.objects.filter(
            status='online',
            user__in=[room.user, room.admin] if room.admin else [room.user]
        )

        context = {
            'room': room,
            'room_id_str': str(room.id),
            'chat_messages': chat_messages,
            'online_users': online_users,
            'is_deleted_by_user': is_deleted_by_user,
        }

        return render(request, 'chat/chat_room.html', context)

    except ChatRoom.DoesNotExist:
        from django.contrib import messages as django_messages
        django_messages.error(request, 'چت مورد نظر یافت نشد.')
        return redirect('chat:chat_list')


@login_required
@require_POST
def mark_message_as_read(request, message_id):
    try:
        message = ChatMessage.objects.get(id=message_id)

        if not request.user.is_staff and request.user != message.room.user:
            return JsonResponse({'success': False, 'error': 'شما اجازه دسترسی به این پیام را ندارید.'})

        if message.is_read:
            return JsonResponse({'success': True, 'already_read': True})

        message.is_read = True
        message.save()

        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{message.room.id}',
                {
                    'type': 'message_read',
                    'message_id': str(message.id),
                    'read_by_user_id': request.user.id
                }
            )
        except Exception as e:
            print(f"Error sending to channel: {e}")

        return JsonResponse({'success': True})

    except ChatMessage.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'پیام مورد نظر یافت نشد.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def start_chat(request):
    if request.user.is_staff:
        return redirect('chat:admin_dashboard')

    if request.method == 'POST':
        existing_active_chat = ChatRoom.objects.filter(
            user=request.user,
            is_active=True
        ).exclude(
            id__in=DeletedChat.objects.filter(user=request.user).values('room_id')
        ).first()

        if existing_active_chat:
            return redirect('chat:chat_room', room_id=existing_active_chat.id)

        new_chat = ChatRoom.objects.create(
            user=request.user,
            is_active=True
        )

        admin_user = User.objects.filter(is_staff=True).first()
        sender = admin_user if admin_user else request.user

        ChatMessage.objects.create(
            room=new_chat,
            content="به پشتیبانی زیما خوش آمدید. چگونه می‌توانیم به شما کمک کنیم؟",
            message_type="system",
            sender=sender
        )

        admins = User.objects.filter(is_staff=True)
        for admin in admins:
            pass

        return redirect('chat:chat_room', room_id=new_chat.id)

    if request.user.is_staff:
        return redirect('chat:admin_dashboard')

    return render(request, 'chat/start_chat.html')

@login_required
@require_POST
def delete_chat(request, room_id):
    """حذف (مخفی کردن) چت برای کاربر"""
    try:
        room = ChatRoom.objects.get(id=room_id)

        if room.user != request.user and not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'error': 'شما اجازه حذف این گفتگو را ندارید'
            })

        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{room_id}',
                {
                    'type': 'chat_deleted',
                    'deleted_by': request.user.username,
                    'deleted_by_id': request.user.id,
                    'is_staff': request.user.is_staff
                }
            )
        except Exception as e:
            print(f"Error sending delete notification: {e}")

        if request.user.is_staff:
            room.delete()
            return JsonResponse({'success': True})
        else:
            DeletedChat.objects.get_or_create(user=request.user, room=room)
            return JsonResponse({'success': True})

    except ChatRoom.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'گفتگوی مورد نظر یافت نشد'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_POST
def close_chat(request, room_id):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'شما اجازه بستن این چت را ندارید'})

    try:
        room = ChatRoom.objects.get(id=room_id)

        room.is_active = False
        room.save()

        ChatMessage.objects.create(
            room=room,
            content='این گفتگو توسط پشتیبانی بسته شده است.',
            message_type='system',
            sender=request.user
        )

        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{room_id}',
                {
                    'type': 'chat_status_update',
                    'is_closed': True,
                    'message': 'این گفتگو توسط پشتیبانی بسته شده است.'
                }
            )
        except ImportError:
            pass

        return JsonResponse({'success': True})

    except ChatRoom.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'گفتگوی مورد نظر یافت نشد'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



@login_required
def assign_admin(request, room_id):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'دسترسی غیرمجاز'})

    try:
        room = ChatRoom.objects.get(id=room_id)
        room.admin = request.user
        room.save()

        room.participants.add(request.user)

        ChatMessage.objects.create(
            room=room,
            content=f'این چت به {request.user.get_full_name() or request.user.username} اختصاص یافت.',
            message_type='system',
            sender=request.user
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{room_id}',
            {
                'type': 'user_status_update',
                'message': f'این چت به {request.user.get_full_name() or request.user.username} اختصاص یافت.'
            }
        )

        return JsonResponse({'success': True})

    except ChatRoom.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'چت مورد نظر یافت نشد'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('chat:chat_list')

    active_chats = ChatRoom.objects.filter(is_active=True).count()

    pending_rooms = ChatRoom.objects.filter(
        is_active=True,
        admin__isnull=True
    ).order_by('-created_at')

    for room in pending_rooms:
        room.last_message = room.messages.order_by('-created_at').first()

    pending_chats = pending_rooms.count()

    online_users = UserChatStatus.objects.filter(status='online').count()

    admin_active_chats = ChatRoom.objects.filter(
        is_active=True,
        admin=request.user
    ).order_by('-updated_at')

    for room in admin_active_chats:
        room.unread_count = room.messages.filter(
            is_read=False,
            sender=room.user
        ).count()
        room.last_message = room.messages.order_by('-created_at').first()

    context = {
        'active_chats': active_chats,
        'pending_chats': pending_chats,
        'online_users': online_users,
        'pending_rooms': pending_rooms,
        'admin_active_chats': admin_active_chats,
    }

    return render(request, 'chat/admin_dashboard.html', context)


# @login_required
# @require_POST
# def mark_message_read(request, message_id):
#     """علامت‌گذاری پیام به عنوان خوانده شده"""
#     try:
#         message = ChatMessage.objects.get(id=message_id)
#
#         # فقط پیام‌هایی که برای کاربر فعلی هستند را علامت‌گذاری کن
#         if message.room.user == request.user or request.user.is_staff:
#             if not message.is_read and message.sender != request.user:
#                 message.is_read = True
#                 message.save()
#
#                 # ارسال وضعیت خوانده شدن به وب‌سوکت
#                 try:
#                     from channels.layers import get_channel_layer
#                     from asgiref.sync import async_to_sync
#
#                     channel_layer = get_channel_layer()
#                     async_to_sync(channel_layer.group_send)(
#                         f'chat_{message.room.id}',
#                         {
#                             'type': 'message_read',
#                             'message_id': str(message_id),
#                             'read_by_user_id': request.user.id
#                         }
#                     )
#                 except Exception as e:
#                     print(f"Error sending to channel: {e}")
#
#                 return JsonResponse({'success': True})
#             else:
#                 return JsonResponse({'success': True, 'info': 'پیام قبلاً خوانده شده است'})
#         else:
#             return JsonResponse({'success': False, 'error': 'شما اجازه دسترسی به این پیام را ندارید'})
#
#     except ChatMessage.DoesNotExist:
#         return JsonResponse({'success': False, 'error': 'پیام مورد نظر یافت نشد'})
#     except Exception as e:
#         return JsonResponse({'success': False, 'error': str(e)})


def api_pending_chats(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'دسترسی غیرمجاز'})

    pending_rooms = ChatRoom.objects.filter(is_active=True, admin=None).order_by('-created_at')

    for room in pending_rooms:
        room.last_message = room.messages.order_by('-created_at').first()

    html = render_to_string('chat/partials/pending_chats.html', {'pending_rooms': pending_rooms})

    return JsonResponse({'success': True, 'html': html})


def api_active_chats(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'دسترسی غیرمجاز'})

    admin_active_chats = ChatRoom.objects.filter(is_active=True, admin=request.user).order_by('-updated_at')

    for room in admin_active_chats:
        room.unread_count = room.messages.filter(is_read=False, sender=room.user).count()
        room.last_message = room.messages.order_by('-created_at').first()

    # تبدیل به HTML
    html = render_to_string('chat/partials/active_chats.html', {'admin_active_chats': admin_active_chats})

    return JsonResponse({'success': True, 'html': html})


@login_required
def notifications(request):
    user_notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:20]

    context = {
        'notifications': user_notifications
    }
    return render(request, 'chat/notifications.html', context)


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'نوتیفیکیشن یافت نشد'})


@login_required
def notification_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def create_support_chat(request):
    if request.user.is_staff:
        return redirect('chat:admin_dashboard')

    existing_active_chat = ChatRoom.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    if existing_active_chat:
        return redirect('chat:chat_room', room_id=existing_active_chat.id)

    new_chat = ChatRoom.objects.create(
        user=request.user,
        is_active=True
    )

    ChatMessage.objects.create(
        room=new_chat,
        content="به پشتیبانی زیما خوش آمدید. چگونه می‌توانیم به شما کمک کنیم؟",
        message_type="system",
        sender=request.user  # تعیین کاربر فعلی به عنوان فرستنده
    )

    return redirect('chat:chat_room', room_id=new_chat.id)


@login_required
def reopen_chat(request, room_id):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'شما اجازه بازگشایی این چت را ندارید'})

    try:
        room = ChatRoom.objects.get(id=room_id)

        room.is_active = True
        room.save()

        ChatMessage.objects.create(
            room=room,
            content='این چت بازگشایی شده است.',
            message_type='system',
            sender=request.user
        )

        # ارسال پیام به کانال وب‌سوکت
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{room_id}',
            {
                'type': 'chat_status_update',
                'is_closed': False,
                'message': 'این چت توسط ادمین بازگشایی شده است.'
            }
        )

        return JsonResponse({'success': True})

    except ChatRoom.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'چت مورد نظر یافت نشد'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def api_unread_counts(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'دسترسی غیرمجاز'})

    user_unread_count = 0
    admin_unread_count = 0

    if request.user.is_staff:
        admin_unread_count = ChatMessage.objects.filter(
            room__admin=request.user,
            is_read=False,
            sender__is_staff=False
        ).count()

        pending_count = ChatRoom.objects.filter(
            is_active=True,
            admin=None
        ).count()

        admin_unread_count += pending_count
    else:
        user_unread_count = ChatMessage.objects.filter(
            room__user=request.user,
            is_read=False
        ).exclude(sender=request.user).count()

    return JsonResponse({
        'success': True,
        'user_unread_count': user_unread_count,
        'admin_unread_count': admin_unread_count
    })


class SetUserOfflineView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Authentication required'}, status=403)

        try:
            status, created = UserChatStatus.objects.get_or_create(user=request.user)
            status.status = 'offline'
            status.save()

            # اطلاع‌رسانی به اتاق‌های چت
            from .signals import notify_status_change
            notify_status_change(request.user, 'offline')

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


def check_online_status():
    # زمان فعلی منهای 2 دقیقه
    threshold = timezone.now() - timedelta(minutes=2)

    # کاربرانی که آخرین فعالیت آنها قبل از threshold است را آفلاین کن
    offline_users = UserChatStatus.objects.filter(
        status='online',
        last_activity__lt=threshold
    )

    for user_status in offline_users:
        user_status.status = 'offline'
        user_status.save()

        # اطلاع‌رسانی به اتاق‌های چت
        from .signals import notify_status_change
        notify_status_change(user_status.user, 'offline')

class SetUserOnlineView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Authentication required'}, status=403)

        try:
            status, created = UserChatStatus.objects.get_or_create(user=request.user)
            status.status = 'online'
            status.last_activity = timezone.now()
            status.save()

            # اطلاع‌رسانی به اتاق‌های چت
            from .signals import notify_status_change
            notify_status_change(request.user, 'online')

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

def unread_count(request):
    """دریافت تعداد پیام‌های خوانده نشده"""
    if not request.user.is_authenticated:
        return JsonResponse({'count': 0})

    try:
        if request.user.is_staff:
            # برای ادمین: تعداد کل پیام‌های خوانده نشده در تمام چت‌ها
            admin_unread_count = ChatMessage.objects.filter(
                room__admin=request.user,
                is_read=False,
                sender__is_staff=False  # فقط پیام‌های کاربران عادی
            ).count()

            # اضافه کردن تعداد چت‌های در انتظار
            pending_count = ChatRoom.objects.filter(
                is_active=True,
                admin=None
            ).count()

            count = admin_unread_count + pending_count
        else:
            # برای کاربر عادی: تعداد پیام‌های خوانده نشده در چت‌های خودش
            count = ChatMessage.objects.filter(
                room__user=request.user,
                is_read=False,
                sender__is_staff=True  # فقط پیام‌های ادمین
            ).count()

        return JsonResponse({'count': count})
    except Exception as e:
        return JsonResponse({'count': 0, 'error': str(e)})


@login_required
def get_user_status(request, user_id):
    """API برای دریافت وضعیت آنلاین/آفلاین یک کاربر"""
    try:
        user = User.objects.get(id=user_id)
        status_obj = UserChatStatus.objects.filter(user=user).first()

        if status_obj:
            return JsonResponse({'status': status_obj.status})
        else:
            return JsonResponse({'status': 'offline'})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




