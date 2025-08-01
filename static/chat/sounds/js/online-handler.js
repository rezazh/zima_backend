// static/chat/js/online-handler.js
(function() {
    'use strict';

    // جلوگیری از اجرای مکرر
    if (window.ZimaOnlineHandler) {
        console.log('Online handler already initialized');
        return;
    }

    window.ZimaOnlineHandler = {
        socket: null,
        isConnected: false,
        isConnecting: false,
        lastActivity: Date.now(),
        heartbeatInterval: null,

        init: function() {
            console.log('Initializing online handler');
            this.setupBeforeUnload();

            // فقط یک اتصال WebSocket برای وضعیت آنلاین
            setTimeout(() => this.connect(), 3000);
        },

        connect: function() {
            if (this.isConnecting || this.isConnected) {
                return;
            }

            this.isConnecting = true;

            try {
                const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${wsProtocol}//${window.location.host}/ws/online-status/`;

                this.socket = new WebSocket(wsUrl);

                this.socket.onopen = () => {
                    console.log('Online status connected');
                    this.isConnected = true;
                    this.isConnecting = false;
                    this.sendOnlineStatus();
                    this.startHeartbeat();
                };

                this.socket.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    if (data.type === 'status_update') {
                        this.updateUserStatus(data.user_id, data.status);
                    } else if (data.type === 'all_statuses') {
                        for (const userId in data.statuses) {
                            this.updateUserStatus(userId, data.statuses[userId]);
                        }
                    }
                };

                this.socket.onclose = () => {
                    console.log('Online status disconnected');
                    this.isConnected = false;
                    this.isConnecting = false;
                    this.stopHeartbeat();
                };

                this.socket.onerror = (error) => {
                    console.error('Online status error:', error);
                    this.isConnecting = false;
                };

            } catch (error) {
                console.error('Error creating online status socket:', error);
                this.isConnecting = false;
            }
        },

        setupBeforeUnload: function() {
            window.addEventListener('beforeunload', () => {
                this.sendOfflineStatus();
            });
        },

        sendOnlineStatus: function() {
            if (this.isConnected && this.socket) {
                this.socket.send(JSON.stringify({
                    type: 'set_status',
                    status: 'online'
                }));
            }
        },

        sendOfflineStatus: function() {
            if (this.isConnected && this.socket) {
                try {
                    this.socket.send(JSON.stringify({
                        type: 'offline'
                    }));
                } catch (e) {
                    console.error('Error sending offline status:', e);
                }
            }
        },

        startHeartbeat: function() {
            this.stopHeartbeat();
            this.heartbeatInterval = setInterval(() => {
                if (this.isConnected && this.socket) {
                    this.socket.send(JSON.stringify({
                        type: 'heartbeat'
                    }));
                }
            }, 120000); // 2 دقیقه
        },

        stopHeartbeat: function() {
            if (this.heartbeatInterval) {
                clearInterval(this.heartbeatInterval);
                this.heartbeatInterval = null;
            }
        },

        updateUserStatus: function(userId, status) {
            const elements = document.querySelectorAll(`.user-status[data-user-id="${userId}"]`);
            elements.forEach(element => {
                element.classList.remove('online', 'offline');
                element.classList.add(status);
                element.setAttribute('title', status === 'online' ? 'آنلاین' : 'آفلاین');

                const statusDot = element.querySelector('.status-dot');
                if (statusDot) {
                    statusDot.classList.remove('online', 'offline');
                    statusDot.classList.add(status);
                }
            });
        }
    };

    // شروع فقط یک بار
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.ZimaOnlineHandler.init();
        });
    } else {
        window.ZimaOnlineHandler.init();
    }

})();