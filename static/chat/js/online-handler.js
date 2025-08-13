(function() {
    'use strict';

    if (window.ZimaOnlineHandler) return;

    window.ZimaOnlineHandler = {
        socket: null,
        isConnected: false,
        isConnecting: false,
        heartbeatInterval: null,
        heartbeatDelay: 60000,
        reconnectDelay: 3000,

        init: function() {
            this.setupBeforeUnload();
            this.setupActivityListeners();
            setTimeout(() => this.connect(), this.reconnectDelay);
        },

        connect: function() {
            if (this.isConnecting || this.isConnected) return;

            this.isConnecting = true;
            try {
                const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${wsProtocol}//${window.location.host}/ws/online-status/`;
                this.socket = new WebSocket(wsUrl);

                this.socket.onopen = () => {
                    this.isConnected = true;
                    this.isConnecting = false;
                    this.sendOnlineStatus();
                    this.startHeartbeat();
                };

                this.socket.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        if (data.type === 'online_status_update') {
                            this.updateUserStatus(data.user_id, data.status);
                        } else if (data.type === 'all_statuses') {
                            for (const uid in data.statuses) {
                                this.updateUserStatus(uid, data.statuses[uid]);
                            }
                        }
                    } catch (err) {}
                };

                this.socket.onclose = () => {
                    this.isConnected = false;
                    this.isConnecting = false;
                    this.stopHeartbeat();
                    setTimeout(() => this.connect(), this.reconnectDelay);
                };

                this.socket.onerror = () => {
                    this.isConnecting = false;
                };

            } catch (error) {
                this.isConnecting = false;
            }
        },

        setupBeforeUnload: function() {
            window.addEventListener('beforeunload', () => {
                this.sendOfflineStatus();
            });
        },

        setupActivityListeners: function() {
            document.addEventListener('mousemove', () => this.sendHeartbeatNow());
            document.addEventListener('keydown', () => this.sendHeartbeatNow());
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
            if (this.isConnected && this.socket && this.socket.readyState === WebSocket.OPEN) {
                try {
                    this.socket.send(JSON.stringify({ type: 'offline' }));
                } catch {}
            }
        },

        startHeartbeat: function() {
            this.stopHeartbeat();
            this.heartbeatInterval = setInterval(() => {
                this.sendHeartbeatNow();
            }, this.heartbeatDelay);
        },

        stopHeartbeat: function() {
            if (this.heartbeatInterval) {
                clearInterval(this.heartbeatInterval);
                this.heartbeatInterval = null;
            }
        },

        sendHeartbeatNow: function() {
            if (this.isConnected && this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify({ type: 'heartbeat' }));
            }
        },

        updateUserStatus: function(userId, status) {
            const elements = document.querySelectorAll(`.user-status[data-user-id="${userId}"]`);
            elements.forEach(element => {
                element.classList.remove('online', 'offline');
                element.classList.add(status);
                element.setAttribute('title', status === 'online' ? 'آنلاین' : 'آفلاین');
                const dot = element.querySelector('.status-dot');
                if (dot) {
                    dot.classList.remove('online', 'offline');
                    dot.classList.add(status);
                }
            });
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.ZimaOnlineHandler.init();
        });
    } else {
        window.ZimaOnlineHandler.init();
    }
})();