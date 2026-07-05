// Управление сообщениями персоны
class PersonMessages {
    constructor() {
        this.messages = [];
        this.editingMessageId = null;
        this.init();
    }

    init() {
        this.bindEvents();
    }

    /**
     * Привязка событий
     */
    bindEvents() {
        // Кнопка добавления сообщения
        const addBtn = document.getElementById('addMessageBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => {
                this.addMessageSimple();
            });
        }
    }

    /**
     * Добавление нового сообщения с красивым интерфейсом
     */
    addMessageSimple() {
        this.showMessageModal();
    }

    /**
     * Показ модального окна для добавления/редактирования сообщения
     */
    showMessageModal(message = null) {
        // Удаляем существующий модал если есть
        this.hideMessageModal();

        const isEdit = message !== null;
        const modalTitle = isEdit ? 'Редактировать сообщение' : 'Добавить новое сообщение';
        const submitText = isEdit ? 'Сохранить изменения' : 'Добавить сообщение';
        const messageText = isEdit ? message.text : '';

        const modal = document.createElement('div');
        modal.className = 'message-modal-overlay';
        modal.innerHTML = `
            <div class="message-modal">
                <div class="message-modal-header">
                    <h3 class="message-modal-title">${modalTitle}</h3>
                    <button class="message-modal-close" type="button">✕</button>
                </div>
                <div class="message-modal-body">
                    <div class="message-form">
                        <div class="form-group">
                            <label for="messageText" class="form-label">Текст сообщения</label>
                            <textarea 
                                id="messageText" 
                                class="form-textarea" 
                                placeholder="Введите текст сообщения или заметку..."
                                rows="6"
                            >${messageText}</textarea>
                            <div class="form-help">
                                Вы можете добавить важные заметки, воспоминания или любую другую информацию о данной персоне.
                            </div>
                        </div>
                    </div>
                </div>
                <div class="message-modal-footer">
                    <button type="button" class="btn btn-secondary message-modal-cancel">Отмена</button>
                    <button type="button" class="btn btn-primary message-modal-submit">${submitText}</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Фокус на textarea
        setTimeout(() => {
            const textarea = modal.querySelector('#messageText');
            textarea.focus();
            if (messageText) {
                textarea.setSelectionRange(messageText.length, messageText.length);
            }
        }, 100);

        // Привязываем события
        this.bindModalEvents(modal, message);
    }

    /**
     * Привязка событий модального окна
     */
    bindModalEvents(modal, existingMessage = null) {
        const closeBtn = modal.querySelector('.message-modal-close');
        const cancelBtn = modal.querySelector('.message-modal-cancel');
        const submitBtn = modal.querySelector('.message-modal-submit');
        const textarea = modal.querySelector('#messageText');

        // Закрытие модала
        const closeModal = () => this.hideMessageModal();

        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);

        // Закрытие по клику на overlay
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });

        // Закрытие по Escape
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);

        // Автоизменение размера textarea
        textarea.addEventListener('input', () => {
            textarea.style.height = 'auto';
            textarea.style.height = textarea.scrollHeight + 'px';
        });

        // Отправка формы
        const handleSubmit = () => {
            const text = textarea.value.trim();
            if (!text) {
                textarea.focus();
                textarea.classList.add('error');
                setTimeout(() => textarea.classList.remove('error'), 2000);
                return;
            }

            if (existingMessage) {
                this.updateMessage(existingMessage.id, text);
            } else {
                this.addMessage(text);
            }

            closeModal();
        };

        submitBtn.addEventListener('click', handleSubmit);

        // Отправка по Ctrl+Enter
        textarea.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                handleSubmit();
            }
        });
    }

    /**
     * Скрытие модального окна
     */
    hideMessageModal() {
        const modal = document.querySelector('.message-modal-overlay');
        if (modal) {
            modal.remove();
        }
    }

    /**
     * Загрузка сообщений
     */
    async loadMessages(personId) {
        try {
            const messagesList = document.getElementById('messagesList');
            if (!messagesList) {
                console.warn('Элемент messagesList не найден');
                return;
            }

            // Показываем индикатор загрузки
            messagesList.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Загрузка сообщений...</p>
                </div>
            `;

            const url = `/api/person/${personId}/messages`;
            console.log('Загружаем сообщения с URL:', url);

            const response = await fetch(url);
            console.log('Ответ сервера:', response.status, response.statusText);

            if (!response.ok) {
                throw new Error(`Ошибка загрузки сообщений: ${response.status}`);
            }

            const rawData = await response.json();
            console.log('Получены данные:', rawData);

            // Преобразуем сложный формат данных в простые сообщения
            this.messages = this.convertLegacyMessages(rawData);
            console.log('Преобразованные сообщения:', this.messages);

            this.renderMessages();

        } catch (error) {
            console.error('Ошибка при загрузке сообщений:', error);
            const messagesList = document.getElementById('messagesList');
            if (messagesList) {
                messagesList.innerHTML = `
                    <div class="error-message">
                        <h3>Ошибка загрузки сообщений</h3>
                        <p>Не удалось загрузить сообщения. Попробуйте обновить страницу.</p>
                        <p class="error-details">Ошибка: ${error.message}</p>
                        <button class="btn js-reload">Обновить</button>
                    </div>
                `;
            }
        }
    }

    /**
     * Преобразование старого формата сообщений в новый
     */
    convertLegacyMessages(rawData) {
        const messages = [];

        if (!Array.isArray(rawData)) {
            console.warn('rawData не является массивом:', rawData);
            return messages;
        }

        rawData.forEach((item, index) => {
            // Если это уже новый формат (с полем text)
            if (item.text !== undefined) {
                messages.push({
                    id: item.id || `msg_${Date.now()}_${index}`,
                    text: item.text,
                    timestamp: item.timestamp || new Date().toISOString(),
                    updatedAt: item.updatedAt || item.edited || item.editedAt
                });
            }
            // Если это старый формат (с полем type и content)
            else if (item.type === 'text') {
                messages.push({
                    id: item.id || `legacy_${Date.now()}_${index}`,
                    text: item.content,
                    timestamp: item.date || item.editedDate || new Date().toISOString(),
                    updatedAt: item.editedDate
                });
            }
            // Пропускаем другие типы (например, albums)
        });

        return messages;
    }

    /**
     * Отображение сообщений
     */
    renderMessages() {
        const container = document.getElementById('messagesList');
        if (!container) {
            console.warn('Элемент messagesList не найден для рендеринга');
            return;
        }

        if (this.messages.length === 0) {
            this.showEmptyState();
            return;
        }

        const messagesHTML = this.messages.map((message, index) =>
            this.createMessageHTML(message, index)
        ).join('');

        container.innerHTML = messagesHTML;
        this.bindMessageEvents();
    }

    /**
     * Создание HTML для сообщения
     */
    createMessageHTML(message, index) {
        const date = new Date(message.timestamp || Date.now()).toLocaleString('ru-RU');
        const messageId = message.id || index;

        return `
            <div class="message-item" data-index="${index}" data-id="${messageId}">
                <div class="message-header">
                    <div class="message-icon">💬</div>
                    <div class="message-actions">
                        <button class="btn btn-sm edit-message" data-index="${index}" data-id="${messageId}" title="Редактировать">
                            ✏️
                        </button>
                        <button class="btn btn-sm btn-danger delete-message" data-index="${index}" data-id="${messageId}" title="Удалить">
                            🗑️
                        </button>
                    </div>
                </div>
                <div class="message-content">
                    <p class="message-text">${this.escapeHtml(message.text)}</p>
                </div>
                <div class="message-meta">
                    <span class="message-date">${date}</span>
                    ${message.updatedAt ? `<span class="message-updated">(изменено ${new Date(message.updatedAt).toLocaleString('ru-RU')})</span>` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Привязка событий к сообщениям
     */
    bindMessageEvents() {
        const container = document.getElementById('messagesList');
        if (!container) return;

        // Редактирование
        container.querySelectorAll('.edit-message').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.closest('button').dataset.index);
                this.editMessage(index);
            });
        });

        // Удаление
        container.querySelectorAll('.delete-message').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.closest('button').dataset.index);
                this.deleteMessage(index);
            });
        });
    }

    /**
     * Добавление нового сообщения
     */
    async addMessage(text) {
        try {
            const newMessage = {
                id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                text: text,
                timestamp: new Date().toISOString()
            };

            this.messages.unshift(newMessage);
            await this.saveMessages();
            this.renderMessages();

            if (window.showSuccess) {
                showSuccess('Сообщение добавлено');
            }

        } catch (error) {
            console.error('Ошибка добавления сообщения:', error);
            if (window.showError) {
                showError('Ошибка добавления сообщения');
            }
        }
    }

    /**
     * Обновление существующего сообщения
     */
    async updateMessage(messageId, text) {
        try {
            const messageIndex = this.messages.findIndex(msg => msg.id === messageId);
            if (messageIndex === -1) {
                throw new Error('Сообщение не найдено');
            }

            this.messages[messageIndex] = {
                ...this.messages[messageIndex],
                text: text,
                updatedAt: new Date().toISOString()
            };

            await this.saveMessages();
            this.renderMessages();

            if (window.showSuccess) {
                showSuccess('Сообщение обновлено');
            }

        } catch (error) {
            console.error('Ошибка обновления сообщения:', error);
            if (window.showError) {
                showError('Ошибка обновления сообщения');
            }
        }
    }

    /**
     * Редактирование сообщения
     */
    editMessage(index) {
        const message = this.messages[index];
        if (message) {
            this.showMessageModal(message);
        }
    }

    /**
     * Удаление сообщения
     */
    async deleteMessage(index) {
        if (!confirm('Удалить это сообщение?')) {
            return;
        }

        try {
            this.messages.splice(index, 1);
            await this.saveMessages();
            this.renderMessages();

            if (window.showSuccess) {
                showSuccess('Сообщение удалено');
            }

        } catch (error) {
            console.error('Ошибка удаления сообщения:', error);
            if (window.showError) {
                showError('Ошибка удаления сообщения');
            }
        }
    }

    /**
     * Сохранение сообщений на сервер
     */
    async saveMessages() {
        try {
            const personId = window.getPersonIdFromUrl ? getPersonIdFromUrl() : this.getPersonIdFromUrl();
            const response = await fetch(`/api/person/${personId}/messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.messages)
            });

            if (!response.ok) {
                throw new Error('Ошибка сохранения сообщений');
            }

        } catch (error) {
            console.error('Ошибка сохранения сообщений:', error);
            throw error;
        }
    }

    /**
     * Получение ID персоны из URL (fallback)
     */
    getPersonIdFromUrl() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('id');
    }

    /**
     * Показать пустое состояние
     */
    showEmptyState() {
        const container = document.getElementById('messagesList');
        if (!container) return;

        container.innerHTML = `
            <div class="messages-empty">
                <div class="messages-empty-icon">💬</div>
                <h3 class="messages-empty-text">Нет сообщений</h3>
                <p class="messages-empty-hint">Добавьте первое сообщение или заметку о данной персоне</p>
            </div>
        `;
    }

    /**
     * Экранирование HTML
     */
    escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Экспорт для использования в других модулях
window.PersonMessages = PersonMessages;
