from zima import settings

from asgiref.sync import async_to_sync
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Count, F
from django.contrib import messages
from django.urls import reverse
from channels.layers import get_channel_layer  # مشکل 1 حل شد
from django.contrib.auth import get_user_model
from .models import ChatRoom, ChatMessage, Notification, UserStatus, TemporaryFile



User = get_user_model()  # این خط مدل User را برای استفاده آماده می‌کند

@login_required
def chat_list(request):
    """
    نمایش لیست گفتگوهای کاربر
    """
    user = request.user

    if user.is_staff:
        # برای کاربران پشتیبان، فقط گفتگوهای باز اختصاص داده شده به خودشان
        rooms = ChatRoom.objects.filter(
            agent=user,            status='open',
            is_deleted_by_agent=False
        ).annotate(
            unread_count=Count('messages', filter=Q(messages__is_read=False, messages__sender=F('user')))
        ).order_by('-updated_at')
    else:
        # برای کاربران عادی، فقط گفتگوهای خودشان که حذف نکرده‌اند
        rooms = ChatRoom.objects.filter(            user=user,
            is_deleted_by_user=False
        ).annotate(
            unread_count=Count('messages', filter=Q(messages__is_read=False, messages__sender=F('agent')))
        ).order_by('-updated_at')

    context = {
        'rooms': rooms,
    }

    return render(request, 'chat/chat_list.html', context)


@login_required
def chat_room(request, room_id):
    """
    نمایش صفحه گفتگو و علامت‌گذاری پیام‌ها به عنوان خوانده شده
    """
    user = request.user
    room = get_object_or_404(ChatRoom, id=room_id)

    # بررسی دسترسی کاربر به اتاق    if user.is_staff:
    can_access = False
    if user.is_staff:
        # ادمین به تمام چت‌هایی که توسط خودش حذف نشده دسترسی دارد
        if not room.is_deleted_by_agent:
            can_access = True
    else:
        # کاربر عادی به چت خودش که حذف نکرده دسترسی دارد
        if room.user == user and not room.is_deleted_by_user:
            can_access = True

    if not can_access:
        messages.error(request, "شما به این گفتگو دسترسی ندارید.")
        redirect_url = 'chat:admin_dashboard' if user.is_staff else 'chat:chat_list'
        return redirect(redirect_url)

    chat_messages = room.messages.all().order_by('created_at')

    # ✅ شروع منطق حل مشکل تیک دوم (خوانده شدن آنی)
    unread_messages = chat_messages.filter(is_read=False).exclude(sender=user)
    if unread_messages.exists():
        message_ids_to_update = list(unread_messages.values_list('id', flat=True))

        now = timezone.now()
        # آپدیت گروهی پیام‌ها در دیتابیس
        unread_messages.update(is_read=True, read_at=now)

        channel_layer = get_channel_layer()
        for message_id in message_ids_to_update:
            async_to_sync(channel_layer.group_send)(
                f'chat_{room_id}',
                {
                    'type': 'message_read',
                    'message_id': str(message_id),
                    'user_id': str(user.id),  # کاربری که پیام را خوانده
                    'read_at': now.isoformat()
                }
            )
    # ✅ پایان منطق حل مشکل تیک دوم

    context = {
        'room': room,
        'chat_messages': chat_messages,
    }
    return render(request, 'chat/chat_room.html', context)


@login_required
def start_chat(request):

    user = request.user
    if user.is_staff:
        messages.error(request, "کاربران پشتیبان نمی‌توانند گفتگوی جدید ایجاد کنند.")
        return redirect('chat:admin_dashboard')

    existing_open_room = ChatRoom.objects.filter(user=user, status='open', is_deleted_by_user=False).first()
    if existing_open_room:
        return redirect('chat:room', room_id=existing_open_room.id)

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if not subject or not message:
            messages.error(request, "لطفاً موضوع و پیام خود را وارد کنید.")
            return render(request, 'chat/start_chat.html')

        new_room = ChatRoom.objects.create(name=subject, user=user, status='open')
        ChatMessage.objects.create(room=new_room, sender=user, content=message, message_type='text')

        # ایجاد اعلان برای همه پشتیبان‌های فعال
        for admin in User.objects.filter(is_staff=True, is_active=True):
            Notification.objects.create(
                user=admin,
                title="گفتگوی جدید",
                message=f"گفتگوی جدید از {user.username}: {subject}",
                notification_type="chat",
                data={"room_id": str(new_room.id)}
            )

        # ✅ شروع تغییر: ارسال رویداد به داشبورد ادمین
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'admin_dashboard',
            {
                'type': 'dashboard.update',
                'event_type': 'new_chat',
                'data': {
                    'room_id': str(new_room.id),
                    'room_name': new_room.name,
                    'user_id': new_room.user.id,
                    'username': new_room.user.username,
                    'created_at': new_room.created_at.strftime('%Y-%m-%d %H:%M'),
                    'url': reverse('chat:room', args=[new_room.id])
                }
            }
        )
        # ✅ پایان تغییر

        return redirect('chat:room', room_id=new_room.id)

    return render(request, 'chat/start_chat.html')


@login_required
@require_POST
def hide_room(request, room_id):
    """پنهان کردن (حذف نرم) یک گفتگو"""
    try:
        room = ChatRoom.objects.get(id=room_id)

        if request.user != room.user and not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'شما اجازه دسترسی به این گفتگو را ندارید'}, status=403)

        if request.user == room.user:
            room.is_deleted_by_user = True
        elif request.user.is_staff:
            room.is_deleted_by_agent = True
        room.save()

        # اطلاع‌رسانی به کلاینت‌های دیگر در همان روم
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{room_id}',
            {
                'type': 'chat.deleted.by.user',  # این نوع رویداد در chat.js شما هندل می‌شود
                'message': f'این گفتگو توسط {request.user.username} حذف شد.'
            }
        )
        return JsonResponse({'success': True})
    except ChatRoom.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'گفتگو یافت نشد'}, status=404)


@login_required
def admin_dashboard(request):
    """
    داشبورد مدیریت برای پشتیبان‌ها با قابلیت جستجو و نمایش پیام‌های خوانده نشده
    """
    if not request.user.is_staff:
        messages.error(request, "شما به این صفحه دسترسی ندارید.")
        return redirect('chat:chat_list')
    search_query = request.GET.get('q', '')
    closed_search_query = request.GET.get('closed_q', '')

    search_results = None
    if search_query:
        search_results = ChatRoom.objects.filter(
            Q(name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(messages__content__icontains=search_query)
        ).distinct().order_by('-updated_at')
        for room in search_results:
            matching_messages = room.messages.filter(content__icontains=search_query).order_by('-created_at')
            if matching_messages.exists():
                room.matching_message = matching_messages.first()

    # ✅ شروع منطق حل مشکل اول (شمارش پیام در داشبورد)
    # گفتگوهای بدون پشتیبان
    unassigned_rooms = ChatRoom.objects.filter(agent__isnull=True, status='open').annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender__is_staff=True))
    ).order_by('-created_at')

    # گفتگوهای اختصاص داده شده به این پشتیبان
    my_rooms = ChatRoom.objects.filter(agent=request.user, status='open', is_deleted_by_agent=False).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False, messages__sender=F('user')))    ).order_by('-updated_at')

    # گفتگوهای در حال انجام (اختصاص داده شده به سایر پشتیبان‌ها)
    assigned_rooms = ChatRoom.objects.filter(agent__isnull=False, status='open').exclude(agent=request.user).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender__is_staff=True))
    ).order_by('-updated_at')
    # ✅ پایان منطق حل مشکل اول    # گفتگوهای بسته شده با امکان جستجو
    closed_rooms_query = ChatRoom.objects.filter(status='closed')
    if closed_search_query:
        closed_rooms_query = closed_rooms_query.filter(
            Q(name__icontains=closed_search_query) |            Q(user__username__icontains=closed_search_query) |
            Q(messages__content__icontains=closed_search_query)
        ).distinct()
    # نمایش گفتگوهای بسته‌ای که توسط ادمین فعلی حذف نشده‌اند
    closed_rooms = closed_rooms_query.filter(is_deleted_by_agent=False).order_by('-closed_at')

    context = {
        'unassigned_rooms': unassigned_rooms,
        'my_rooms': my_rooms,
        'assigned_rooms': assigned_rooms,
        'closed_rooms': closed_rooms,
        'search_results': search_results,
        'search_query': search_query,
        'closed_search_query': closed_search_query,
    }
    return render(request, 'chat/admin_dashboard.html', context)


@login_required
@require_POST
def assign_room(request, room_id):
    """اختصاص دادن گفتگو به پشتیبان"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'شما به این عملیات دسترسی ندارید.'}, status=403)

    room = get_object_or_404(ChatRoom, id=room_id)
    if room.status != 'open':
        return JsonResponse({'success': False, 'error': 'این گفتگو قابل اختصاص نیست.'}, status=400)

    room.agent = request.user
    room.save(update_fields=['agent'])

    ChatMessage.objects.create(
        room=room,
        content=f"پشتیبان {request.user.username} به گفتگو پیوست.",
        message_type='system'
    )

    # ✅ شروع تغییر: ارسال رویداد به داشبورد ادمین
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'admin_dashboard',
        {
            'type': 'dashboard.update',
            'event_type': 'chat_assigned',
            'data': {
                'room_id': str(room.id),
                'agent_id': request.user.id,
                'agent_name': request.user.username,
                # ارسال اطلاعات کامل برای ساخت آیتم
                'room_name': room.name,
                'user_id': room.user.id,
                'username': room.user.username,
                'updated_at': room.updated_at.strftime('%H:%M'),
                'url': reverse('chat:room', args=[room.id])
            }
        }
    )    # ✅ پایان تغییر

    return JsonResponse({'success': True, 'redirect_url': reverse('chat:room', args=[room.id])})


@login_required
@require_POST
def close_room(request, room_id):
    user = request.user
    room = get_object_or_404(ChatRoom, id=room_id)

    if not (user.is_staff or room.user == user):
        return JsonResponse({'success': False, 'error': 'شما به این گفتگو دسترسی ندارید.'}, status=403)

    if room.status != 'open':
        return JsonResponse({'success': False, 'error': 'این گفتگو قبلاً بسته شده است.'}, status=400)

    room.close(user)

    # ✅ شروع تغییر: ارسال رویداد به داشبورد ادمین
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'admin_dashboard',
        {
            'type': 'dashboard.update',
            'event_type': 'chat_closed',
            'data': {
                'room_id': str(room.id),
                # ارسال اطلاعات کامل برای ساخت آیتم
                'room_name': room.name,
                'user_id': room.user.id,
                'username': room.user.username,
                'agent_name': room.agent.username if room.agent else '',
                'closed_at': room.closed_at.strftime('%Y-%m-%d %H:%M'),
                'url': reverse('chat:room', args=[room.id])
            }        }
    )
    # ✅ پایان تغییر

    # بازگشت به داشبورد برای تجربه کاربری بهتر ادمین
    redirect_url = reverse('chat:admin_dashboard') if user.is_staff else reverse('chat:chat_list')
    return JsonResponse({'success': True, 'redirect_url': redirect_url})


@login_required
@require_POST
def reopen_room(request, room_id):
    """بازگشایی گفتگو"""
    user = request.user
    room = get_object_or_404(ChatRoom, id=room_id)

    if not (user.is_staff or room.user == user):
        return JsonResponse({'success': False, 'error': 'شما به این گفتگو دسترسی ندارید.'}, status=403)

    if room.status != 'closed':
        return JsonResponse({'success': False, 'error': 'این گفتگو قابل بازگشایی نیست.'}, status=400)
    success = room.reopen(user)
    if not success:
        return JsonResponse({'success': False, 'error': 'بازگشایی گفتگو با خطا مواجه شد.'}, status=400)

    return JsonResponse({'success': True})


@login_required
@require_GET
def get_unread_count(request):
    """دریافت تعداد کل پیام‌های خوانده نشده برای کاربر"""
    user = request.user
    count = 0
    if user.is_staff:
        # برای ادمین، همه پیام‌های خوانده‌نشده از طرف کاربران در چت‌های باز
        count = ChatMessage.objects.filter(
            room__status='open',
            room__is_deleted_by_agent=False,
            is_read=False,
            sender__is_staff=False
        ).count()
    else:
        # برای کاربران عادی، پیام‌های خوانده‌نشده از طرف پشتیبان در چت‌های خودشان
        count = ChatMessage.objects.filter(
            room__user=user,
            room__is_deleted_by_user=False,
            is_read=False,
            sender__is_staff=True
        ).count()

    return JsonResponse({'count': count})


# سایر توابع کمکی که نیازی به تغییر نداشتند
@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    context = {'notifications': notifications}
    return render(request, 'chat/notifications.html', context)@login_required
@require_POST
def mark_message_read(request, message_id):
    message = get_object_or_404(ChatMessage, id=message_id)
    room = message.room
    user = request.user

    if not (user.is_staff or room.user == user):
        return JsonResponse({'success': False, 'error': 'شما به این پیام دسترسی ندارید.'}, status=403)

    if message.sender != user and not message.is_read:
        message.is_read = True
        message.read_at = timezone.now()
        message.save(update_fields=['is_read', 'read_at'])
    return JsonResponse({'success': True})


@login_required
@require_POST
def set_online(request):
    UserStatus.objects.update_or_create(
        user=request.user,
        defaults={'status': 'online', 'last_seen': timezone.now()}
    )
    return JsonResponse({'success': True})


@login_required
@csrf_exempt
@require_POST
def set_offline(request):
    UserStatus.objects.update_or_create(
        user=request.user,
        defaults={'status': 'offline'}
    )
    return HttpResponse(status=204)


@login_required
@require_POST
def upload_temp_file(request):
    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'فایلی انتخاب نشده است.'}, status=400)

    file = request.FILES['file']
    if file.size > 5 * 1024 * 1024:
        return JsonResponse({'success': False, 'error': 'حداکثر اندازه فایل 5 مگابایت است.'}, status=400)

    temp_file = TemporaryFile.objects.create(user=request.user, file=file)
    return JsonResponse({
        'success': True,
        'file_id': str(temp_file.id),
        'file_name': file.name,
        'file_url': temp_file.file.url
    })