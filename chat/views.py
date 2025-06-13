from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Count, Max, F
from django.contrib import messages
from django.urls import reverse

from .consumers import User
from .models import ChatRoom, ChatMessage, Notification, UserStatus, TemporaryFile


@login_required
def chat_list(request):
    """
    نمایش لیست گفتگوهای کاربر
    """
    user = request.user

    # دریافت لیست گفتگوها بر اساس نوع کاربر
    if user.is_staff:
        # برای کاربران پشتیبان، تمام گفتگوهای غیر حذف شده
        rooms = ChatRoom.objects.filter(
            Q(is_deleted_by_agent=False)
        ).annotate(
            unread_count=Count('messages', filter=Q(messages__is_read=False, messages__sender=F('user')))
        ).order_by('-updated_at')
    else:
        # برای کاربران عادی، فقط گفتگوهای خودشان
        rooms = ChatRoom.objects.filter(
            user=user,
            is_deleted_by_user=False
        ).annotate(
            unread_count=Count('messages', filter=Q(messages__is_read=False, messages__sender=F('agent')))
        ).order_by('-updated_at')

    context = {
        'rooms': rooms,
    }

    return render(request, 'chat/chat_list.html', context)


def chat_room(request, room_id):
    """
    نمایش صفحه گفتگو
    """
    user = request.user

    # دریافت اتاق گفتگو
    room = get_object_or_404(ChatRoom, id=room_id)

    # بررسی دسترسی کاربر به اتاق
    if user.is_staff:
        if room.is_deleted_by_agent:
            messages.error(request, "این گفتگو حذف شده است.")
            return redirect('chat:chat_list')
    else:
        if room.user != user or room.is_deleted_by_user:
            messages.error(request, "شما به این گفتگو دسترسی ندارید.")
            return redirect('chat:chat_list')

    # دریافت پیام‌های گفتگو
    chat_messages = room.messages.all().order_by('created_at')

    # علامت‌گذاری پیام‌های خوانده نشده به عنوان خوانده شده
    unread_messages = chat_messages.filter(is_read=False).exclude(sender=user)
    for message in unread_messages:
        message.is_read = True
        message.read_at = timezone.now()
        message.save(update_fields=['is_read', 'read_at'])

    context = {
        'room': room,
        'chat_messages': chat_messages,  # تغییر نام متغیر از messages به chat_messages
    }

    return render(request, 'chat/chat_room.html', context)

@login_required
def start_chat(request):
    """
    شروع گفتگوی جدید
    """
    user = request.user

    # کاربران پشتیبان نمی‌توانند گفتگوی جدید ایجاد کنند
    if user.is_staff:
        messages.error(request, "کاربران پشتیبان نمی‌توانند گفتگوی جدید ایجاد کنند.")
        return redirect('chat:chat_list')

    # بررسی وجود گفتگوی باز قبلی
    existing_open_room = ChatRoom.objects.filter(
        user=user,
        status='open',
        is_deleted_by_user=False
    ).first()

    if existing_open_room:
        return redirect('chat:room', room_id=existing_open_room.id)

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if not subject or not message:
            messages.error(request, "لطفاً موضوع و پیام خود را وارد کنید.")
            return render(request, 'chat/start_chat.html')

        # ایجاد گفتگوی جدید
        new_room = ChatRoom.objects.create(
            name=subject,
            user=user,
            room_type='support',
            status='open'
        )

        # ایجاد پیام اولیه
        ChatMessage.objects.create(
            room=new_room,
            sender=user,
            content=message,
            message_type='text'
        )

        # ایجاد اعلان برای پشتیبان‌ها
        for admin in User.objects.filter(is_staff=True):
            Notification.objects.create(
                user=admin,
                title="گفتگوی جدید",
                message=f"گفتگوی جدید از {user.username}: {subject}",
                notification_type="chat",
                data={
                    "room_id": str(new_room.id)
                }
            )

        return redirect('chat:room', room_id=new_room.id)

    return render(request, 'chat/start_chat.html')


@login_required
def hide_room(request, room_id):
    """پنهان کردن (حذف نرم) یک گفتگو برای کاربر"""
    if request.method == 'POST':
        try:
            room = ChatRoom.objects.get(id=room_id)

            # بررسی دسترسی کاربر
            if request.user != room.user and not request.user.is_staff:
                return JsonResponse({'success': False, 'error': 'شما اجازه دسترسی به این گفتگو را ندارید'}, status=403)

            # اضافه کردن کاربر به لیست کاربران پنهان کننده
            room.hidden_for_users.add(request.user)

            # علامت‌گذاری به عنوان حذف شده
            if request.user == room.user:
                room.mark_deleted_by_user()
            elif request.user.is_staff:
                room.mark_deleted_by_agent()

            room.save()

            # اطلاع‌رسانی به کاربران دیگر از طریق وب‌سوکت
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{room_id}',
                {
                    'type': 'chat_deleted_by_user',
                    'room_id': str(room.id),
                    'username': request.user.username  # ارسال نام کاربر به جای deleted_by
                }
            )

            return JsonResponse({'success': True})
        except ChatRoom.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'گفتگو یافت نشد'}, status=404)

    return JsonResponse({'success': False, 'error': 'درخواست نامعتبر'}, status=400)


@login_required
def admin_dashboard(request):
    """
    داشبورد مدیریت گفتگوها برای پشتیبان‌ها
    """
    user = request.user

    # فقط کاربران پشتیبان می‌توانند به این صفحه دسترسی داشته باشند
    if not user.is_staff:
        messages.error(request, "شما به این صفحه دسترسی ندارید.")
        return redirect('chat:chat_list')

    # گفتگوهای باز بدون پشتیبان
    unassigned_rooms = ChatRoom.objects.filter(
        status='open',
        agent__isnull=True
    ).order_by('-created_at')

    # گفتگوهای باز با پشتیبان
    assigned_rooms = ChatRoom.objects.filter(
        status='open',
        agent__isnull=False
    ).order_by('-updated_at')

    # گفتگوهای بسته شده
    closed_rooms = ChatRoom.objects.filter(
        status='closed'
    ).order_by('-closed_at')

    # گفتگوهای آرشیو شده
    archived_rooms = ChatRoom.objects.filter(
        status='archived'
    ).order_by('-updated_at')

    # گفتگوهای اختصاص داده شده به این پشتیبان
    my_rooms = ChatRoom.objects.filter(
        agent=user,
        status='open',
        is_deleted_by_agent=False
    ).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False, messages__sender=F('user')))
    ).order_by('-updated_at')

    context = {
        'unassigned_rooms': unassigned_rooms,
        'assigned_rooms': assigned_rooms,
        'closed_rooms': closed_rooms,
        'archived_rooms': archived_rooms,
        'my_rooms': my_rooms,
    }

    return render(request, 'chat/admin_dashboard.html', context)


@login_required
@require_POST
def assign_room(request, room_id):
    """
    اختصاص دادن گفتگو به پشتیبان
    """
    user = request.user

    # فقط کاربران پشتیبان می‌توانند گفتگو را اختصاص دهند
    if not user.is_staff:
        return JsonResponse({'success': False, 'error': 'شما به این عملیات دسترسی ندارید.'}, status=403)

    room = get_object_or_404(ChatRoom, id=room_id)

    # بررسی وضعیت گفتگو
    if room.status != 'open':
        return JsonResponse({'success': False, 'error': 'این گفتگو قابل اختصاص نیست.'}, status=400)

    # اختصاص دادن گفتگو به پشتیبان
    room.agent = user
    room.save(update_fields=['agent'])

    # ایجاد پیام سیستمی
    ChatMessage.objects.create(
        room=room,
        content=f"پشتیبان {user.username} به گفتگو پیوست.",
        message_type='system'
    )

    return JsonResponse({
        'success': True,
        'redirect_url': reverse('chat:room', args=[room.id])
    })


@login_required
def notifications_view(request):
    """
    نمایش لیست اعلان‌های کاربر
    """
    user = request.user

    # دریافت اعلان‌های کاربر
    notifications = Notification.objects.filter(user=user).order_by('-created_at')

    context = {
        'notifications': notifications,
    }

    return render(request, 'chat/notifications.html', context)


@login_required
@require_POST
def mark_message_read(request, message_id):
    """
    علامت‌گذاری پیام به عنوان خوانده شده
    """
    user = request.user

    message = get_object_or_404(ChatMessage, id=message_id)

    # بررسی دسترسی کاربر به پیام
    room = message.room
    if user.is_staff:
        if room.is_deleted_by_agent:
            return JsonResponse({'success': False, 'error': 'شما به این پیام دسترسی ندارید.'}, status=403)
    else:
        if room.user != user or room.is_deleted_by_user:
            return JsonResponse({'success': False, 'error': 'شما به این پیام دسترسی ندارید.'}, status=403)

    # فقط پیام‌های دریافتی را می‌توان به عنوان خوانده شده علامت‌گذاری کرد
    if message.sender != user and not message.is_read:
        message.is_read = True
        message.read_at = timezone.now()
        message.save(update_fields=['is_read', 'read_at'])

    return JsonResponse({'success': True})


@login_required
@require_POST
def close_room(request, room_id):
    """
    بستن گفتگو
    """
    user = request.user

    room = get_object_or_404(ChatRoom, id=room_id)

    # بررسی دسترسی کاربر به اتاق
    if user.is_staff:
        if room.is_deleted_by_agent:
            return JsonResponse({'success': False, 'error': 'شما به این گفتگو دسترسی ندارید.'}, status=403)
    else:
        if room.user != user or room.is_deleted_by_user:
            return JsonResponse({'success': False, 'error': 'شما به این گفتگو دسترسی ندارید.'}, status=403)

    # بررسی وضعیت اتاق
    if room.status != 'open':
        return JsonResponse({'success': False, 'error': 'این گفتگو قبلاً بسته شده است.'}, status=400)

    # بستن اتاق
    room.close(user)

    return JsonResponse({'success': True})


@login_required
@require_POST
def reopen_room(request, room_id):
    """
    بازگشایی گفتگو
    """
    user = request.user

    room = get_object_or_404(ChatRoom, id=room_id)

    # بررسی دسترسی کاربر به اتاق
    if user.is_staff:
        if room.is_deleted_by_agent:
            return JsonResponse({'success': False, 'error': 'شما به این گفتگو دسترسی ندارید.'}, status=403)
    else:
        if room.user != user or room.is_deleted_by_user:
            return JsonResponse({'success': False, 'error': 'شما به این گفتگو دسترسی ندارید.'}, status=403)

    # بررسی وضعیت اتاق
    if room.status != 'closed':
        return JsonResponse({'success': False, 'error': 'این گفتگو قابل بازگشایی نیست.'}, status=400)

    # بازگشایی اتاق
    success = room.reopen(user)

    if not success:
        return JsonResponse({'success': False, 'error': 'بازگشایی گفتگو با خطا مواجه شد.'}, status=400)

    return JsonResponse({'success': True})


@login_required
@require_POST
def set_online(request):
    """تنظیم وضعیت کاربر به آنلاین"""
    user_status, created = UserStatus.objects.get_or_create(user=request.user)
    user_status.status = 'online'
    user_status.save(update_fields=['status', 'last_seen'])

    return JsonResponse({'success': True})


@login_required
@csrf_exempt
@require_POST
def set_offline(request):
    """تنظیم وضعیت کاربر به آفلاین"""
    user_status, created = UserStatus.objects.get_or_create(user=request.user)
    user_status.status = 'offline'
    user_status.save(update_fields=['status', 'last_seen'])

    return HttpResponse(status=204)


@login_required
@require_GET
def get_unread_count(request):
    """دریافت تعداد پیام‌های خوانده نشده"""
    user = request.user

    # محاسبه تعداد پیام‌های خوانده نشده
    if user.is_staff:
        # برای کاربران پشتیبان، تعداد پیام‌های خوانده نشده در تمام گفتگوهای باز
        count = ChatMessage.objects.filter(
            room__status='open',
            room__is_deleted_by_agent=False,
            is_read=False,
            sender__isnull=False  # پیام‌های سیستمی را نادیده می‌گیریم
        ).exclude(sender=user).count()
    else:
        # برای کاربران عادی، تعداد پیام‌های خوانده نشده در گفتگوهای خودشان
        count = ChatMessage.objects.filter(
            room__user=user,
            room__is_deleted_by_user=False,
            is_read=False,
            sender__isnull=False  # پیام‌های سیستمی را نادیده می‌گیریم
        ).exclude(sender=user).count()

    return JsonResponse({'count': count})


@login_required
@require_POST
def upload_temp_file(request):
    """آپلود فایل موقت"""
    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'فایلی انتخاب نشده است.'}, status=400)

    file = request.FILES['file']

    # بررسی اندازه فایل (حداکثر 5MB)
    if file.size > 5 * 1024 * 1024:
        return JsonResponse({'success': False, 'error': 'حداکثر اندازه فایل 5 مگابایت است.'}, status=400)

    # ذخیره فایل موقت
    temp_file = TemporaryFile.objects.create(
        user=request.user,
        file=file
    )

    return JsonResponse({
        'success': True,
        'file_id': str(temp_file.id),
        'file_name': file.name,
        'file_url': temp_file.file.url
    })

def get_rooms_for_user(user):
    """دریافت لیست اتاق‌های گفتگو برای کاربر"""
    if user.is_staff:
        # برای کاربران ادمین، اتاق‌های اختصاص داده شده به آنها را برگردان
        return ChatRoom.objects.filter(agent=user).order_by('-updated_at')
    else:
        # برای کاربران عادی، اتاق‌هایی که آنها ایجاد کرده‌اند یا در آنها مشارکت دارند را برگردان
        # به جز اتاق‌هایی که کاربر آنها را حذف کرده است
        return ChatRoom.objects.filter(
            (Q(user=user) | Q(participants=user)) &
            ~Q(hidden_for_users=user)
        ).distinct().order_by('-updated_at')


def admin_dashboard(request):
    """نمایش داشبورد مدیریت برای پشتیبان‌ها"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('chat:chat_list')

    # دریافت پارامتر جستجوی کلی
    search_query = request.GET.get('q', '')
    closed_search_query = request.GET.get('closed_q', '')

    # جستجو در تمام گفتگوها
    search_results = None
    if search_query:
        # استفاده از Q objects برای ترکیب شروط جستجو
        from django.db.models import Q

        search_results = ChatRoom.objects.filter(
            Q(name__icontains=search_query) |
            Q(messages__content__icontains=search_query)
        ).distinct()

        # افزودن پیام‌های منطبق با جستجو به هر گفتگو
        for room in search_results:
            matching_messages = room.messages.filter(content__icontains=search_query).order_by('-created_at')
            if matching_messages.exists():
                room.matching_message = matching_messages.first()

    # گفتگوهای بدون پشتیبان
    unassigned_rooms = ChatRoom.objects.filter(agent__isnull=True, status='open')

    # گفتگوهای اختصاص داده شده به این پشتیبان
    my_rooms = ChatRoom.objects.filter(agent=request.user, status='open')

    # گفتگوهای در حال انجام (اختصاص داده شده به سایر پشتیبان‌ها)
    assigned_rooms = ChatRoom.objects.filter(agent__isnull=False, status='open').exclude(agent=request.user)

    # گفتگوهای بسته شده با امکان جستجو
    closed_rooms = ChatRoom.objects.filter(status='closed')

    if closed_search_query:
        # استفاده از Q objects برای جستجو در گفتگوهای بسته شده
        from django.db.models import Q

        closed_rooms = closed_rooms.filter(
            Q(name__icontains=closed_search_query) |
            Q(messages__content__icontains=closed_search_query)
        ).distinct()

    # مرتب‌سازی گفتگوهای بسته شده
    # اگر فیلد closed_at وجود دارد، از آن استفاده کنید، در غیر این صورت از updated_at استفاده کنید
    try:
        closed_rooms = closed_rooms.order_by('-closed_at')
    except:
        closed_rooms = closed_rooms.order_by('-updated_at')

    context = {
        'unassigned_rooms': unassigned_rooms,
        'my_rooms': my_rooms,
        'assigned_rooms': assigned_rooms,
        'closed_rooms': closed_rooms,
        'search_results': search_results,
    }

    return render(request, 'chat/admin_dashboard.html', context)
