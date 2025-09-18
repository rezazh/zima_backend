document.addEventListener('DOMContentLoaded', function() {
    const roomId = document.getElementById('room-id').value;
    const userId = document.getElementById('user-id').value;
    const isStaff = document.getElementById('is-staff').value === 'True';
    const messageContainer = document.getElementById('message-container');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const closeRoomButton = document.getElementById('close-room-button');
    const reopenRoomButton = document.getElementById('reopen-room-button');
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileInput = document.getElementById('file-input');
    const roomStatus = document.getElementById('room-status');
    const typingIndicator = document.getElementById('typing-indicator');
    const notificationSound = document.getElementById('notification-sound');
    const chatActions = document.querySelector('.chat-actions');

    let typingTimeout = null;
    let socket = null;
    let tempFileId = null;
    let tempFilePreview = null;

    console.log('Chat room loaded');
    console.log('Is staff:', isStaff);
    console.log('User ID:', userId);
    console.log('Room elements:', {
        closeButton: closeRoomButton,
        reopenButton: reopenRoomButton,
        messageInput: messageInput,
        sendButton: sendButton
    });

    // اتصال به وب‌سوکت
    function connectWebSocket() {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        socket = new WebSocket(
            `${wsProtocol}//${window.location.host}/ws/chat/${roomId}/`
        );

        socket.onopen = function(e) {
            console.log('WebSocket connected');

            // علامت‌گذاری پیام‌های خوانده نشده به عنوان خوانده شده
            document.querySelectorAll('.message.received:not(.read)').forEach(function(messageElement) {
                const messageId = messageElement.id.replace('message-', '');
                if (messageId && !messageId.startsWith('system-')) {
                    markMessageAsRead(messageId);
                }
            });
        };

        socket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            console.log('WebSocket message received:', data);

            if (data.type === 'room_status') {
                console.log('Room status update received:', data);
                handleRoomStatusChange(data);
            }
            else if (data.type === 'chat.deleted_by_user') {
                // پردازش پیام حذف گفتگو توسط کاربر
                handleChatDeleted(data);
            }
            else if (data.type === 'chat_message') {
                // دریافت پیام جدید
                appendMessage(data.message);

                // پخش صدای اعلان اگر پیام از کاربر دیگر است
                if (data.message.sender_id !== userId) {
                    notificationSound.play().catch(error => console.error('Error playing notification sound:', error));
                }

                // اسکرول به پایین
                messageContainer.scrollTop = messageContainer.scrollHeight;

                // علامت‌گذاری پیام به عنوان خوانده شده اگر از کاربر دیگر است
                if (data.message.sender_id !== userId && data.message.message_type !== 'system') {
                    markMessageAsRead(data.message.id);
                }
            }
            else if (data.type === 'message_read') {
                // به‌روزرسانی وضعیت خوانده شدن پیام
                const messageElement = document.getElementById('message-' + data.message_id);
                if (messageElement) {
                    const readIndicator = messageElement.querySelector('.read-indicator');
                    if (readIndicator) {
                        readIndicator.innerHTML = '<i class="fas fa-check-double"></i>';
                        readIndicator.setAttribute('title', 'خوانده شده در ' + new Date(data.read_at).toLocaleString('fa-IR'));
                        messageElement.classList.add('read');
                    }
                }
            }
            else if (data.type === 'user_typing') {
                // نمایش وضعیت تایپ کردن کاربر
                if (data.user_id !== userId) {
                    typingIndicator.textContent = data.username + ' در حال تایپ است...';
                    typingIndicator.style.display = data.is_typing ? 'block' : 'none';
                }
            }
            else if (data.type === 'error') {
                // نمایش خطا
                showNotification(data.message, 'danger');
            }
        };

        socket.onclose = function(e) {
            console.log('WebSocket disconnected, trying to reconnect in 2 seconds...');
            setTimeout(function() {
                connectWebSocket();
            }, 2000);
        };

        socket.onerror = function(e) {
            console.error('WebSocket error:', e);
        };
    }

    // مدیریت تغییر وضعیت اتاق
    function handleRoomStatusChange(data) {
        // به‌روزرسانی نشانگر وضعیت
        if (roomStatus) {
            roomStatus.textContent = data.status === 'open' ? 'باز' : 'بسته شده';
            roomStatus.className = `badge ${data.status === 'open' ? 'bg-success' : 'bg-danger'} mx-2`;
        }

        // فعال/غیرفعال کردن ورودی پیام
        if (messageInput) messageInput.disabled = data.status !== 'open';
        if (sendButton) sendButton.disabled = data.status !== 'open';
        if (fileUploadButton) fileUploadButton.disabled = data.status !== 'open';

        // به‌روزرسانی دکمه‌های بستن و بازگشایی
        updateActionButtons(data);

        // اضافه کردن پیام سیستمی به چت
        if (data.message) {
            appendMessage({
                id: 'system-' + Date.now(),
                content: data.message,
                message_type: 'system',
                created_at: new Date().toISOString()
            });

            // اسکرول به پایین
            messageContainer.scrollTop = messageContainer.scrollHeight;
        }

        // نمایش اعلان
        if (data.status === 'closed') {
            const notificationText = data.closed_by_staff ?
                'این گفتگو توسط پشتیبانی بسته شده است.' :
                'این گفتگو توسط کاربر بسته شده است.';

            showNotification(notificationText, 'warning');
        } else if (data.status === 'open' && data.message) {
            showNotification(data.message, 'success');
        }
    }

    // به‌روزرسانی دکمه‌های بستن و بازگشایی
    function updateActionButtons(data) {
        // پاک کردن محتوای قبلی
        if (chatActions) {
            chatActions.innerHTML = '';

            // ایجاد دکمه مناسب بر اساس وضعیت
            if (data.status === 'open') {
                // اتاق باز است، نمایش دکمه بستن
                const closeButton = document.createElement('button');
                closeButton.id = 'close-room-button';
                closeButton.className = 'btn btn-danger btn-sm';
                closeButton.innerHTML = '<i class="fas fa-times"></i> بستن گفتگو';
                closeButton.addEventListener('click', closeRoom);
                chatActions.appendChild(closeButton);
            } else {
                // اتاق بسته است، تصمیم‌گیری برای نمایش دکمه بازگشایی
                let showReopenButton = false;

                // شرایط نمایش دکمه بازگشایی
                if (isStaff) {
                    showReopenButton = true;
                    console.log('Admin can reopen the chat');
                } else if (!data.closed_by_staff) {
                    showReopenButton = true;
                    console.log('User can reopen the chat because it was not closed by admin');
                } else {
                    console.log('User cannot reopen the chat because it was closed by admin');
                }

                if (showReopenButton) {
                    const reopenButton = document.createElement('button');
                    reopenButton.id = 'reopen-room-button';
                    reopenButton.className = 'btn btn-success btn-sm';
                    reopenButton.innerHTML = '<i class="fas fa-redo"></i> بازگشایی گفتگو';
                    reopenButton.addEventListener('click', reopenRoom);
                    chatActions.appendChild(reopenButton);
                }
            }
        }
    }

    // اتصال اولیه به وب‌سوکت
    connectWebSocket();
    function handleChatDeleted(data) {
    // نمایش پیام سیستمی در چت
    const messageContainer = document.getElementById('message-container');
    const systemMessage = document.createElement('div');
    systemMessage.className = 'message system-message';
    systemMessage.innerHTML = `
        <div class="message-content">
            <strong class="text-danger">${data.message}</strong>
        </div>
    `;
    messageContainer.appendChild(systemMessage);
    messageContainer.scrollTop = messageContainer.scrollHeight;

    // غیرفعال کردن ارسال پیام
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const fileUploadButton = document.getElementById('file-upload-button');

    messageInput.disabled = true;
    sendButton.disabled = true;
    fileUploadButton.disabled = true;

    messageInput.placeholder = 'این گفتگو توسط کاربر حذف شده است';

    // نمایش اعلان
    showNotification('این گفتگو توسط کاربر حذف شده است', 'warning', 0);
}
    // تابع نمایش اعلان
    function showNotification(message, type, timeout = 5000) {
    // بررسی وجود کانتینر اعلان
    let notificationContainer = document.querySelector('.notification-container');
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.className = 'notification-container';
        document.body.appendChild(notificationContainer);
    }

    // ایجاد اعلان
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.role = 'alert';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // افزودن اعلان به کانتینر
    notificationContainer.appendChild(notification);

    // حذف خودکار اعلان بعد از زمان مشخص شده (اگر timeout صفر باشد، اعلان حذف نمی‌شود)
    if (timeout > 0) {
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 150);
        }, timeout);
    }
}

    // افزودن پیام به صفحه
    function appendMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.id = 'message-' + message.id;
        messageDiv.className = 'message';

        // تعیین کلاس پیام بر اساس فرستنده
        if (message.message_type === 'system') {
            messageDiv.className += ' system-message';
        } else if (message.sender_id === userId) {
            messageDiv.className += ' sent';
        } else {
            messageDiv.className += ' received';
        }

        // اگر پیام خوانده شده است، کلاس read را اضافه می‌کنیم
        if (message.is_read) {
            messageDiv.className += ' read';
        }

        // ایجاد محتوای پیام
        let messageContent = `
            <div class="message-content">
                ${message.content}
            </div>
        `;

        // اگر فایل دارد، آن را نمایش می‌دهیم
        if (message.file_url) {
            const fileUrl = message.file_url;
            const fileExtension = fileUrl.split('.').pop().toLowerCase();
            if (['jpg', 'jpeg', 'png', 'gif'].includes(fileExtension)) {
                messageContent += `
                    <div class="message-image">
                        <a href="${fileUrl}" target="_blank">
                            <img src="${fileUrl}" alt="تصویر پیوست" />
                        </a>
                    </div>
                `;
            } else {
                messageContent += `
                    <div class="message-file">
                        <a href="${fileUrl}" target="_blank">
                            <i class="fas fa-file"></i> دانلود فایل
                        </a>
                    </div>
                `;
            }
        }

        // افزودن اطلاعات پیام (زمان، وضعیت خوانده شدن و ...)
        messageContent += `
            <div class="message-info">
                <span class="message-time">${formatDateTime(message.created_at)}</span>
        `;

        // اگر پیام از کاربر فعلی است، نشانگر خوانده شدن را نمایش می‌دهیم
        if (message.sender_id === userId && message.message_type !== 'system') {
            messageContent += `
                <span class="read-indicator" title="${message.is_read ? 'خوانده شده' : 'ارسال شده'}">
                    <i class="fas ${message.is_read ? 'fa-check-double' : 'fa-check'}"></i>
                </span>
            `;
        }

        messageContent += `</div>`;

        // قرار دادن محتوا در المان پیام
        messageDiv.innerHTML = messageContent;

        // افزودن پیام به صفحه
        messageContainer.appendChild(messageDiv);
    }

    // ارسال پیام
    function sendMessage() {
        const message = messageInput.value.trim();

        if (message || tempFileId) {
            // ارسال پیام به سرور
            socket.send(JSON.stringify({
                'type': 'chat_message',
                'message': message,
                'file_id': tempFileId
            }));

            // پاک کردن ورودی پیام
            messageInput.value = '';

            // پاک کردن پیش‌نمایش فایل
            if (tempFilePreview) {
                tempFilePreview.remove();
                tempFilePreview = null;
            }

            // پاک کردن شناسه فایل موقت
            tempFileId = null;

            // متوقف کردن وضعیت تایپ کردن
            sendTypingStatus(false);
        }
    }

    // آپلود فایل
    function uploadFile() {
        fileInput.click();
    }

    // پردازش انتخاب فایل
    function handleFileSelect(e) {
        const file = e.target.files[0];
        if (!file) return;

        // بررسی اندازه فایل (حداکثر 5MB)
        if (file.size > 5 * 1024 * 1024) {
            alert('حداکثر اندازه فایل 5 مگابایت است.');
            return;
        }

        // ایجاد شیء FormData
        const formData = new FormData();
        formData.append('file', file);

        // ارسال فایل به سرور
        fetch('/chat/api/upload-file/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // ذخیره شناسه فایل موقت
                tempFileId = data.file_id;

                // نمایش پیش‌نمایش فایل
                if (tempFilePreview) {
                    tempFilePreview.remove();
                }

                tempFilePreview = document.createElement('div');
                tempFilePreview.className = 'file-preview';

                const fileExtension = data.file_name.split('.').pop().toLowerCase();
                if (['jpg', 'jpeg', 'png', 'gif'].includes(fileExtension)) {
                    tempFilePreview.innerHTML = `
                        <div class="image-preview">
                            <img src="${data.file_url}" alt="${data.file_name}" />
                            <button type="button" class="btn btn-sm btn-danger remove-file">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    `;
                } else {
                    tempFilePreview.innerHTML = `
                        <div class="file-item">
                            <i class="fas fa-file"></i>
                            <span>${data.file_name}</span>
                            <button type="button" class="btn btn-sm btn-danger remove-file">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    `;
                }

                // افزودن پیش‌نمایش به صفحه
                const chatFooter = document.querySelector('.chat-footer');
                chatFooter.insertBefore(tempFilePreview, messageInput);

                // افزودن رویداد کلیک برای دکمه حذف
                tempFilePreview.querySelector('.remove-file').addEventListener('click', function() {
                    tempFilePreview.remove();
                    tempFilePreview = null;
                    tempFileId = null;
                });
            } else {
                alert('خطا در آپلود فایل: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error uploading file:', error);
            alert('خطا در آپلود فایل. لطفاً مجدداً تلاش کنید.');
        });

        // پاک کردن مقدار input فایل
        fileInput.value = '';
    }

    // علامت‌گذاری پیام به عنوان خوانده شده
    function markMessageAsRead(messageId) {
        socket.send(JSON.stringify({
            'type': 'mark_read',
            'message_id': messageId
        }));
    }

    // ارسال وضعیت تایپ کردن
    function sendTypingStatus(isTyping) {
        socket.send(JSON.stringify({
            'type': 'typing',
            'is_typing': isTyping
        }));
    }

    // بستن اتاق گفتگو
    function closeRoom() {
        if (confirm('آیا از بستن این گفتگو اطمینان دارید؟')) {
            socket.send(JSON.stringify({
                'type': 'close_room'
            }));
        }
    }

    // بازگشایی اتاق گفتگو
    function reopenRoom() {
        if (confirm('آیا از بازگشایی این گفتگو اطمینان دارید؟')) {
            socket.send(JSON.stringify({
                'type': 'reopen_room'
            }));
        }
    }

    // فرمت‌بندی تاریخ و زمان
    function formatDateTime(dateTimeStr) {
        const date = new Date(dateTimeStr);
        return date.toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' }) + ' ' +
               date.toLocaleDateString('fa-IR', { month: 'short', day: 'numeric' });
    }

    // دریافت مقدار کوکی
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // آیا این کوکی با نام مورد نظر شروع می‌شود؟
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // رویدادها

    // ارسال پیام با کلیک روی دکمه
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }

    // ارسال پیام با فشردن Enter
    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // ارسال وضعیت تایپ کردن
        messageInput.addEventListener('input', function() {
            clearTimeout(typingTimeout);

            // ارسال وضعیت تایپ کردن
            sendTypingStatus(true);

            // تنظیم تایمر برای پایان وضعیت تایپ کردن
            typingTimeout = setTimeout(function() {
                sendTypingStatus(false);
            }, 3000);
        });
    }

    // آپلود فایل
    if (fileUploadButton) {
        fileUploadButton.addEventListener('click', uploadFile);
    }

    // انتخاب فایل
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }

    // بستن اتاق گفتگو - افزودن رویداد به دکمه‌های موجود
    if (closeRoomButton) {
        closeRoomButton.addEventListener('click', closeRoom);
    }

    // بازگشایی اتاق گفتگو - افزودن رویداد به دکمه‌های موجود
    if (reopenRoomButton) {
        reopenRoomButton.addEventListener('click', reopenRoom);
    }

    // اسکرول به پایین صفحه
    if (messageContainer) {
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }
});