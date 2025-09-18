document.addEventListener('DOMContentLoaded', function() {
    const userId = document.getElementById('user-id') ? document.getElementById('user-id').value : null;
    const notificationBadge = document.getElementById('notification-badge');
    const notificationList = document.getElementById('notification-list');
    const notificationSound = document.getElementById('notification-sound');

    const chatUnreadBadge = document.getElementById('unread-count');
    const chatHeaderBadge = document.getElementById('chat-notification-badge');

    let socket = null;

    function updateGlobalChatBadges(count) {
        const intCount = parseInt(count, 10);
        if (intCount > 0) {
            if (chatUnreadBadge) {
                chatUnreadBadge.textContent = intCount;                chatUnreadBadge.style.display = 'flex';
            }
            if (chatHeaderBadge) {
                chatHeaderBadge.textContent = intCount;
                chatHeaderBadge.style.display = 'inline-block';
            }
        } else {
            if (chatUnreadBadge) {
                chatUnreadBadge.style.display = 'none';
            }
            if (chatHeaderBadge) {                chatHeaderBadge.style.display = 'none';
            }
        }
    }

    fetch('/chat/unread-count/')
        .then(response => response.json())
        .then(data => {
            updateGlobalChatBadges(data.count);
        })
        .catch(error => console.error('Error fetching initial unread count:', error));

    function connectWebSocket() {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        socket = new WebSocket(
            `${wsProtocol}//${window.location.host}/ws/notifications/`
        );

        socket.onopen = function(e) {
            console.log('Notification WebSocket connected');
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
                const notification = data.notification;
                updateNotificationCount();
                if(notificationSound) {
                    notificationSound.play().catch(error => console.error('Error playing notification sound:', error));
                }
                if (notificationList) {
                    prependNotification(notification);
                }
                showBrowserNotification(notification);
            }
            else if (data.type === 'unread_count') {                updateNotificationBadge(data.count);
            }
            else if (data.type === 'unread_count_update') {
                updateGlobalChatBadges(data.count);
            }
            else if (data.type === 'chat_unread_update') {
                const badges = document.querySelectorAll(`.unread-room-badge[data-room-id="${data.room_id}"]`);
                badges.forEach(badge => {
                    badge.textContent = data.count;
                    badge.style.display = (data.count > 0) ? 'inline-block' : 'none';
                });
            }
            else if (data.type === 'message_read') {
                const roomItems = document.querySelectorAll(`.chat-item a[href$="/${data.room_id}/"]`);
                roomItems.forEach(item => {                    const icon = item.querySelector('.chat-item-message i');
                    if (icon) {
                        icon.classList.remove('fa-check');
                        icon.classList.add('fa-check-double');
                    }
                });
            }
        };

        socket.onclose = function(e) {
            console.log('Notification WebSocket disconnected, trying to reconnect in 2 seconds...');
            setTimeout(function() {                connectWebSocket();
            }, 2000);
        };

        socket.onerror = function(e) {
            console.error('Notification WebSocket error:', e);
        };
    }

    connectWebSocket();

    function updateNotificationCount() {
        fetch('/chat/unread-count/')
            .then(response => response.json())
            .then(data => {
                updateNotificationBadge(data.count);            })
            .catch(error => console.error('Error fetching notification count:', error));
    }    function updateNotificationBadge(count) {
        if (notificationBadge) {
            notificationBadge.textContent = count;
            notificationBadge.style.display = count > 0 ? 'inline-block' : 'none';
        }
    }

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

        if (notification.notification_type === 'chat' && notification.data && notification.data.room_id) {
            notificationContent += `
                <a href="/chat/room/${notification.data.room_id}/" class="btn btn-sm btn-primary">
                    مشاهده گفتگو
                </a>
            `;
        }

        if (!notification.is_read) {
            notificationContent += `
                <button class="btn btn-sm btn-secondary mark-read" data-id="${notification.id}">
                    علامت‌گذاری به عنوان خوانده شده
                </button>
            `;
        }

        notificationContent += `</div>`;

        notificationItem.innerHTML = notificationContent;
        notificationList.insertBefore(notificationItem, notificationList.firstChild);

        const markReadButton = notificationItem.querySelector('.mark-read');
        if (markReadButton) {            markReadButton.addEventListener('click', function() {
                markNotificationAsRead(notification.id);
            });        }
    }

    function markNotificationAsRead(notificationId) {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                'action': 'mark_read',
                'notification_id': notificationId
            }));

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

    function markAllNotificationsAsRead() {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                'action': 'mark_all_read'            }));
            document.querySelectorAll('.notification-item.unread').forEach(function(notificationItem) {
                notificationItem.classList.remove('unread');
                const markReadButton = notificationItem.querySelector('.mark-read');
                if (markReadButton) {
                    markReadButton.remove();
                }
            });
        }
    }

    function showBrowserNotification(notification) {
        if (!('Notification' in window)) return;
        if (Notification.permission === 'granted') {
            createBrowserNotification(notification);
        } else if (Notification.permission !== 'denied') {
            Notification.requestPermission().then(function(permission) {
                if (permission === 'granted') {
                    createBrowserNotification(notification);
                }            });
        }
    }

    function createBrowserNotification(notification) {
        const browserNotification = new Notification(notification.title, {
            body: notification.message,
            icon: '/static/chat/img/notification-icon.png'
        });
        browserNotification.onclick = function() {
            window.focus();
            if (notification.notification_type === 'chat' && notification.data && notification.data.room_id) {
                window.location.href = `/chat/room/${notification.data.room_id}/`;
            } else {
                window.location.href = '/chat/notifications/';
            }            browserNotification.close();
        };
        setTimeout(function() {
            browserNotification.close();        }, 5000);
    }

    function formatDateTime(dateTimeStr) {
        const date = new Date(dateTimeStr);
        return date.toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' }) + ' ' +
               date.toLocaleDateString('fa-IR', { month: 'short', day: 'numeric' });
    }

    const markAllReadButton = document.getElementById('mark-all-read');
    if (markAllReadButton) {        markAllReadButton.addEventListener('click', markAllNotificationsAsRead);
    }

    document.querySelectorAll('.mark-read').forEach(function(button) {
        button.addEventListener('click', function() {            const notificationId = this.getAttribute('data-id');
            markNotificationAsRead(notificationId);        });
    });

    updateNotificationCount();
});