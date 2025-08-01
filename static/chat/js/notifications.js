document.addEventListener('DOMContentLoaded', function() {
    const userId = document.getElementById('user-id').value;
    const notificationBadge = document.getElementById('notification-badge');
    const notificationList = document.getElementById('notification-list');
    const notificationSound = document.getElementById('notification-sound');

    let socket = null;

    // اتصال به وب‌سوکت
    function connectWebSocket() {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        socket = new WebSocket(
            `${wsProtocol}//${window.location.host}/ws/notifications/`
        );

        socket.onopen = function(e) {
            console.log('Notification WebSocket connected');

            // ارسال heartbeat هر 30 ثانیه
            setInterval(function() {
                if (socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify({
                        'action': 'heartbeat'
                    }));
                }
            }, 30000);
        };

        socket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            console.log('Notification WebSocket message received:', data);

            if (data.type === 'notification') {
                // دریافت اعلان جدید
                const notification = data.notification;

                // به‌روزرسانی تعداد اعلان‌های خوانده نشده
                updateNotificationCount();

                // پخش صدای اعلان
                notificationSound.play().catch(error => console.error('Error playing notification sound:', error));

                // اگر صفحه اعلان‌ها باز است، اعلان جدید را نمایش می‌دهیم
                if (notificationList) {
                    prependNotification(notification);
                }

                // نمایش اعلان مرورگر
                showBrowserNotification(notification);
            }
            else if (data.type === 'unread_count') {
                // به‌روزرسانی تعداد اعلان‌های خوانده نشده
                updateNotificationBadge(data.count);
            }
        };

        socket.onclose = function(e) {
            console.log('Notification WebSocket disconnected, trying to reconnect in 2 seconds...');
            setTimeout(function() {
                connectWebSocket();
            }, 2000);
        };

        socket.onerror = function(e) {
            console.error('Notification WebSocket error:', e);
        };
    }

    // اتصال اولیه به وب‌سوکت
    connectWebSocket();

    // به‌روزرسانی تعداد اعلان‌های خوانده نشده
    function updateNotificationCount() {
        fetch('/chat/unread-count/')
            .then(response => response.json())
            .then(data => {
                updateNotificationBadge(data.count);
            })
            .catch(error => console.error('Error fetching notification count:', error));
    }

    // به‌روزرسانی نشانگر تعداد اعلان‌ها
    function updateNotificationBadge(count) {
        if (notificationBadge) {
            notificationBadge.textContent = count;
            notificationBadge.style.display = count > 0 ? 'inline-block' : 'none';
        }
    }

    // افزودن اعلان جدید به لیست
    function prependNotification(notification) {
        const notificationItem = document.createElement('div');
        notificationItem.className = 'notification-item';
        notificationItem.id = 'notification-' + notification.id;

        if (!notification.is_read) {
            notificationItem.classList.add('unread');
        }

        let notificationContent = `
            <div class="notification-header">
                <h5>${notification.title}</h5>
                <span class="notification-time">${formatDateTime(notification.created_at)}</span>
            </div>
            <div class="notification-body">
                <p>${notification.message}</p>
            </div>
            <div class="notification-footer">
        `;

        // اگر نوع اعلان چت است، دکمه مشاهده گفتگو را نمایش می‌دهیم
        if (notification.notification_type === 'chat' && notification.data && notification.data.room_id) {
            notificationContent += `
                <a href="/chat/room/${notification.data.room_id}/" class="btn btn-sm btn-primary">
                    مشاهده گفتگو
                </a>
            `;
        }

        // دکمه علامت‌گذاری به عنوان خوانده شده
        if (!notification.is_read) {
            notificationContent += `
                <button class="btn btn-sm btn-secondary mark-read" data-id="${notification.id}">
                    علامت‌گذاری به عنوان خوانده شده
                </button>
            `;
        }

        notificationContent += `</div>`;

        notificationItem.innerHTML = notificationContent;

        // افزودن به ابتدای لیست
        notificationList.insertBefore(notificationItem, notificationList.firstChild);

        // افزودن رویداد کلیک برای دکمه علامت‌گذاری
        const markReadButton = notificationItem.querySelector('.mark-read');
        if (markReadButton) {
            markReadButton.addEventListener('click', function() {
                markNotificationAsRead(notification.id);
            });
        }
    }

    // علامت‌گذاری اعلان به عنوان خوانده شده
    function markNotificationAsRead(notificationId) {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                'action': 'mark_read',
                'notification_id': notificationId
            }));

            // به‌روزرسانی نمایش اعلان
            const notificationItem = document.getElementById('notification-' + notificationId);
            if (notificationItem) {
                notificationItem.classList.remove('unread');

                const markReadButton = notificationItem.querySelector('.mark-read');
                if (markReadButton) {
                    markReadButton.remove();
                }
            }
        }
    }

    // علامت‌گذاری تمام اعلان‌ها به عنوان خوانده شده
    function markAllNotificationsAsRead() {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                'action': 'mark_all_read'
            }));

            // به‌روزرسانی نمایش اعلان‌ها
            document.querySelectorAll('.notification-item.unread').forEach(function(notificationItem) {
                notificationItem.classList.remove('unread');

                const markReadButton = notificationItem.querySelector('.mark-read');
                if (markReadButton) {
                    markReadButton.remove();
                }
            });
        }
    }

    // نمایش اعلان مرورگر
    function showBrowserNotification(notification) {
        // بررسی پشتیبانی از اعلان‌های مرورگر
        if (!('Notification' in window)) {
            return;
        }

        // درخواست مجوز اعلان
        if (Notification.permission === 'granted') {
            createBrowserNotification(notification);
        }
        else if (Notification.permission !== 'denied') {
            Notification.requestPermission().then(function(permission) {
                if (permission === 'granted') {
                    createBrowserNotification(notification);
                }
            });
        }
    }

    // ایجاد اعلان مرورگر
    function createBrowserNotification(notification) {
        const browserNotification = new Notification(notification.title, {
            body: notification.message,
            icon: '/static/chat/img/notification-icon.png'
        });

        browserNotification.onclick = function() {
            window.focus();

            // اگر اعلان مربوط به چت است، به صفحه گفتگو هدایت می‌کنیم
            if (notification.notification_type === 'chat' && notification.data && notification.data.room_id) {
                window.location.href = `/chat/room/${notification.data.room_id}/`;
            } else {
                window.location.href = '/chat/notifications/';
            }

            browserNotification.close();
        };

        // بستن خودکار اعلان پس از 5 ثانیه
        setTimeout(function() {
            browserNotification.close();
        }, 5000);
    }

    // فرمت‌بندی تاریخ و زمان
    function formatDateTime(dateTimeStr) {
        const date = new Date(dateTimeStr);
        return date.toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' }) + ' ' +
               date.toLocaleDateString('fa-IR', { month: 'short', day: 'numeric' });
    }

    // رویدادها

    // دکمه علامت‌گذاری تمام اعلان‌ها به عنوان خوانده شده
    const markAllReadButton = document.getElementById('mark-all-read');
    if (markAllReadButton) {
        markAllReadButton.addEventListener('click', markAllNotificationsAsRead);
    }

    // دکمه‌های علامت‌گذاری تکی
    document.querySelectorAll('.mark-read').forEach(function(button) {
        button.addEventListener('click', function() {
            const notificationId = this.getAttribute('data-id');
            markNotificationAsRead(notificationId);
        });
    });

    // به‌روزرسانی اولیه تعداد اعلان‌ها
    updateNotificationCount();
});