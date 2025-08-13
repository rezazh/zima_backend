document.addEventListener('DOMContentLoaded', function() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const socket = new WebSocket(
        `${wsProtocol}//${window.location.host}/ws/admin/dashboard/`
    );

    socket.onopen = function(e) {
        console.log('Admin Dashboard WebSocket connected');
    };

    socket.onclose = function(e) {
        console.error('Admin Dashboard WebSocket disconnected. Reconnecting in 5s...');
        setTimeout(() => {
            window.location.reload(); // ساده‌ترین راه برای اتصال مجدد
        }, 5000);
    };

    socket.onmessage = function(e) {
        const event = JSON.parse(e.data);        const eventType = event.type;
        const data = event.data;

        console.log('Dashboard event received:', event);

        if (eventType === 'new_chat') {
            handleNewChat(data);
        } else if (eventType === 'chat_assigned') {
            handleChatAssigned(data);
        } else if (eventType === 'chat_closed') {
            handleChatClosed(data);        }
    };

    function handleNewChat(data) {
        const unassignedList = document.getElementById('unassigned-rooms-list');
        const unassignedCounter = document.getElementById('unassigned-counter');
        const noUnassignedPlaceholder = document.getElementById('no-unassigned-placeholder');

        if (noUnassignedPlaceholder) {
            noUnassignedPlaceholder.style.display = 'none';
        }
        if (unassignedList) {
            unassignedList.style.display = '';
        }

        const newChatItemHTML = `
            <li class="list-group-item d-flex justify-content-between align-items-center" data-room-id="${data.room_id}">
                <a href="${data.url}" class="text-decoration-none text-dark flex-grow-1">
                    <div class="d-flex align-items-center">
                        <span class="fw-bold">${data.room_name}</span>
                        <div class="user-status online" data-user-id="${data.user_id}"><span class="status-dot online"></span></div>
                        <div class="chat-item-badge ms-auto">
                            <div class="badge bg-primary unread-room-badge" data-room-id="${data.room_id}" style="display:none;">0</div>
                        </div>
                    </div>
                    <small class="text-muted">${data.username} - ${data.created_at}</small>
                </a>
                <button class="btn btn-sm btn-primary assign-room ms-2" data-room-id="${data.room_id}">
                    <i class="fas fa-user-plus"></i>
                </button>
            </li>`;

        unassignedList.insertAdjacentHTML('afterbegin', newChatItemHTML);
        unassignedCounter.textContent = parseInt(unassignedCounter.textContent) + 1;
    }

    function handleChatAssigned(data) {
        // از لیست "بدون پشتیبان" حذف کن
        const itemToRemove = document.querySelector(`#unassigned-rooms-list li[data-room-id="${data.room_id}"]`);
        if (itemToRemove) {
            itemToRemove.remove();
            const unassignedCounter = document.getElementById('unassigned-counter');
            unassignedCounter.textContent = Math.max(0, parseInt(unassignedCounter.textContent) - 1);
        }

        // به لیست "گفتگوهای من" اضافه کن
        const myRoomsList = document.getElementById('my-rooms-list');
        const myRoomsCounter = document.getElementById('my-rooms-counter');
        const noMyRoomsPlaceholder = document.getElementById('no-my-rooms-placeholder');

        if (noMyRoomsPlaceholder) {
            noMyRoomsPlaceholder.style.display = 'none';
        }
        if (myRoomsList) {
            myRoomsList.style.display = '';
        }

        const newMyChatItemHTML = `
            <li class="chat-item" data-room-id="${data.room_id}">
                <a href="${data.url}" class="text-decoration-none text-dark d-flex w-100 justify-content-between align-items-center">
                    <div class="chat-item-info">
                        <div class="d-flex align-items-center">
                            <div class="chat-item-title">${data.room_name}</div>
                            <div class="user-status online" data-user-id="${data.user_id}"><span class="status-dot online"></span></div>
                        </div>
                        <div class="chat-item-last-message">اختصاص داده شد</div>
                    </div>
                    <div class="chat-item-meta">
                        <div class="chat-item-time">${data.updated_at}</div>                        <div class="chat-item-badge">
                            <div class="badge bg-primary unread-room-badge" data-room-id="${data.room_id}" style="display:none;">0</div>
                        </div>
                    </div>
                </a>
            </li>`;

        myRoomsList.insertAdjacentHTML('afterbegin', newMyChatItemHTML);
        myRoomsCounter.textContent = parseInt(myRoomsCounter.textContent) + 1;
    }

    function handleChatClosed(data) {
        // از هر لیستی که در آن قرار دارد حذف کن
        const roomItem = document.querySelector(`li[data-room-id="${data.room_id}"]`);
        if (roomItem) {
            const parentList = roomItem.parentElement;
            let counterId = '';
            if (parentList.id === 'unassigned-rooms-list') counterId = 'unassigned-counter';
            else if (parentList.id === 'my-rooms-list') counterId = 'my-rooms-counter';
            else if (parentList.id === 'assigned-rooms-list') counterId = 'assigned-counter';

            roomItem.remove();
            if (counterId) {
                const counter = document.getElementById(counterId);
                counter.textContent = Math.max(0, parseInt(counter.textContent) - 1);
            }
        }

        // به لیست بسته شده اضافه کن
        const closedList = document.getElementById('closed-rooms-list');
        const closedCounter = document.getElementById('closed-counter');
        const noClosedPlaceholder = document.getElementById('no-closed-placeholder');
        if (noClosedPlaceholder) noClosedPlaceholder.style.display = 'none';
        if (closedList) closedList.style.display = '';

        const newClosedItemHTML = `
            <li class="list-group-item d-flex justify-content-between align-items-center" data-room-id="${data.room_id}">
                <div>
                    <span class="fw-bold">${data.room_name}</span><br>
                    <small class="text-muted">
                        ${data.username} - پشتیبان: ${data.agent_name} - بسته شده در: ${data.closed_at}
                    </small>
                </div>
                <a href="${data.url}" class="btn btn-sm btn-outline-secondary"><i class="fas fa-eye"></i> مشاهده</a>
            </li>`;

        closedList.insertAdjacentHTML('afterbegin', newClosedItemHTML);
        closedCounter.textContent = parseInt(closedCounter.textContent) + 1;
    }
});