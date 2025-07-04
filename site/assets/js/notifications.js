// Система уведомлений
class NotificationManager {
    constructor() {
        this.notifications = new Map();
        this.container = null;
        this.maxNotifications = AppConfig.notifications.maxNotifications;
        this.defaultDuration = AppConfig.notifications.defaultDuration;
        this.init();
    }

    init() {
        // Создаем контейнер для уведомлений если его нет
        this.container = document.querySelector('.notifications-container');
        if (!this.container) {
            this.container = Utils.createElement('div', {
                className: 'notifications-container'
            });
            document.body.appendChild(this.container);
        }
    }

    /**
     * Показать уведомление
     * @param {string} message - текст сообщения
     * @param {string} type - тип уведомления (success, error, warning, info)
     * @param {number} duration - время показа в мс (0 для постоянного показа)
     * @param {Object} options - дополнительные опции
     * @returns {string} ID уведомления
     */
    show(message, type = 'info', duration = null, options = {}) {
        const id = Utils.generateId();

        // Ограничиваем количество уведомлений
        if (this.notifications.size >= this.maxNotifications) {
            const oldestId = this.notifications.keys().next().value;
            this.remove(oldestId);
        }

        const notification = this.createNotification(id, message, type, options);
        this.container.appendChild(notification);

        // Анимация появления
        requestAnimationFrame(() => {
            notification.classList.add('show');
        });

        // Сохраняем ссылку
        this.notifications.set(id, {
            element: notification,
            type,
            message,
            timestamp: Date.now()
        });

        // Автоудаление
        if (duration !== 0) {
            const actualDuration = duration || this.defaultDuration;
            setTimeout(() => {
                this.remove(id);
            }, actualDuration);
        }

        return id;
    }

    /**
     * Создание элемента уведомления
     * @param {string} id - ID уведомления
     * @param {string} message - текст сообщения
     * @param {string} type - тип уведомления
     * @param {Object} options - дополнительные опции
     * @returns {HTMLElement} элемент уведомления
     */
    createNotification(id, message, type, options = {}) {
        const notification = Utils.createElement('div', {
            className: `notification ${type}`,
            'data-notification-id': id
        });

        // Иконка
        const icon = Utils.createElement('span', {
            className: 'notification-icon'
        }, AppConfig.icons[type] || AppConfig.icons.info);

        // Сообщение
        const messageElement = Utils.createElement('span', {
            className: 'notification-message'
        }, message);

        // Кнопка закрытия
        const closeButton = Utils.createElement('button', {
            className: 'notification-close',
            type: 'button',
            'aria-label': 'Закрыть уведомление'
        }, '×');

        closeButton.addEventListener('click', () => {
            this.remove(id);
        });

        // Прогресс-бар для таймера (если включен)
        if (options.showTimer !== false) {
            const timer = Utils.createElement('div', {
                className: 'notification-timer'
            });
            notification.appendChild(timer);
        }

        notification.appendChild(icon);
        notification.appendChild(messageElement);
        notification.appendChild(closeButton);

        // Дополнительные обработчики
        if (options.onClick) {
            notification.style.cursor = 'pointer';
            notification.addEventListener('click', options.onClick);
        }

        return notification;
    }

    /**
     * Удаление уведомления
     * @param {string} id - ID уведомления
     */
    remove(id) {
        const notificationData = this.notifications.get(id);
        if (!notificationData) return;

        const element = notificationData.element;

        // Анимация исчезновения
        element.classList.remove('show');

        setTimeout(() => {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
            this.notifications.delete(id);
        }, 300);
    }

    /**
     * Удаление всех уведомлений
     */
    removeAll() {
        Array.from(this.notifications.keys()).forEach(id => {
            this.remove(id);
        });
    }

    /**
     * Удаление уведомлений определенного типа
     * @param {string} type - тип уведомлений для удаления
     */
    removeByType(type) {
        Array.from(this.notifications.entries()).forEach(([id, data]) => {
            if (data.type === type) {
                this.remove(id);
            }
        });
    }

    /**
     * Быстрые методы для разных типов уведомлений
     */
    success(message, duration, options) {
        return this.show(message, 'success', duration, options);
    }

    error(message, duration, options) {
        return this.show(message, 'error', duration, options);
    }

    warning(message, duration, options) {
        return this.show(message, 'warning', duration, options);
    }

    info(message, duration, options) {
        return this.show(message, 'info', duration, options);
    }

    /**
     * Получение количества активных уведомлений
     * @returns {number} количество уведомлений
     */
    getCount() {
        return this.notifications.size;
    }

    /**
     * Получение уведомлений определенного типа
     * @param {string} type - тип уведомлений
     * @returns {Array} массив уведомлений
     */
    getByType(type) {
        return Array.from(this.notifications.values()).filter(data => data.type === type);
    }
}

// Создаем глобальный экземпляр менеджера уведомлений
const notifications = new NotificationManager();

// Глобальная функция для простого показа уведомлений (для обратной совместимости)
function showNotification(message, type = 'info', duration = null) {
    return notifications.show(message, type, duration);
}

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { NotificationManager, notifications, showNotification };
}
