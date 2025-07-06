// Управление сообщениями персоны (упрощенная версия без модальных окон)
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
     * Простое добавление сообщения через prompt
     */
    addMessageSimple() {
        const messageText = prompt('Введите сообщение:');
        if (messageText && messageText.trim()) {
            this.addMessage(messageText.trim());
        }
    }

    /**
     * Загрузка сообщений
     */
    async loadMessages(personId) {
        try {
            const messagesList = document.getElementById('messagesList');
            if (!messagesList) {
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

            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`Ошибка загрузки сообщений: ${response.status}`);
            }

            const rawData = await response.json();

            // Преобразуем сложный формат данных в простые сообщения
            this.messages = this.convertLegacyMessages(rawData);

            this.renderMessages();

        } catch (error) {
            const messagesList = document.getElementById('messagesList');
            if (messagesList) {
                messagesList.innerHTML = `
                    <div class="error-message">
                        <h3>Ошибка загрузки сообщений</h3>
                        <p>Не удалось загрузить сообщения. Попробуйте обновить страницу.</p>
                        <p class="error-details">Ошибка: ${error.message}</p>
                        <button onclick="window.location.reload()" class="btn">Обновить</button>
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

        rawData.forEach(item => {
            // Если это уже новый формат (с полем text)
            if (item.text !== undefined) {
                messages.push({
                    text: item.text,
                    timestamp: item.timestamp || new Date().toISOString(),
                    edited: !!item.edited || !!item.editedAt
                });
            }
            // Если это старый формат (с полем type и content)
            else if (item.type === 'text') {
                messages.push({
                    text: item.content,
                    timestamp: item.date || item.editedDate || new Date().toISOString(),
                    edited: !!item.editedDate
                });
            } else if (item.type === 'album') {
                // Пропускаем альбомы, они обрабатываются в фотографиях
                // или можно добавить специальную обработку
            }
        });

        return messages;
    }

    /**
     * Отображение сообщений
     */
    renderMessages() {
        const container = document.getElementById('messagesList');
        if (!container) {
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
        const isEditing = this.editingMessageId === index;

        return `
            <div class="message-item" data-index="${index}">
                <div class="message-content">
                    ${isEditing ? `
                        <textarea class="edit-textarea" data-index="${index}">${this.escapeHtml(message.text)}</textarea>
                        <div class="edit-actions">
                            <button class="btn btn-sm save-edit" data-index="${index}">Сохранить</button>
                            <button class="btn btn-sm btn-secondary cancel-edit" data-index="${index}">Отмена</button>
                        </div>
                    ` : `
                        <p class="message-text">${this.escapeHtml(message.text)}</p>
                        <div class="message-actions">
                            <button class="btn btn-sm edit-message" data-index="${index}" title="Редактировать">✏️</button>
                            <button class="btn btn-sm btn-danger delete-message" data-index="${index}" title="Удалить">🗑️</button>
                        </div>
                    `}
                </div>
                <div class="message-meta">
                    <span class="message-date">${date}</span>
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
                const index = parseInt(e.target.dataset.index);
                this.editMessage(index);
            });
        });

        // Удаление
        container.querySelectorAll('.delete-message').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.dataset.index);
                this.deleteMessage(index);
            });
        });

        // Сохранение редактирования
        container.querySelectorAll('.save-edit').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.dataset.index);
                this.saveEdit(index);
            });
        });

        // Отмена редактирования
        container.querySelectorAll('.cancel-edit').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.dataset.index);
                this.cancelEdit(index);
            });
        });
    }

    /**
     * Добавление нового сообщения
     */
    async addMessage(text) {
        try {
            const newMessage = {
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
     * Редактирование сообщения
     */
    editMessage(index) {
        this.editingMessageId = index;
        this.renderMessages();
    }

    /**
     * Отмена редактирования
     */
    cancelEdit(index) {
        this.editingMessageId = null;
        this.renderMessages();
    }

    /**
     * Сохранение редактирования
     */
    async saveEdit(index) {
        try {
            const textarea = document.querySelector(`textarea[data-index="${index}"]`);
            if (!textarea) return;

            const newText = textarea.value.trim();
            if (!newText) {
                if (window.showError) {
                    showError('Сообщение не может быть пустым');
                }
                return;
            }

            this.messages[index].text = newText;
            this.messages[index].edited = true;
            this.messages[index].editedAt = new Date().toISOString();

            await this.saveMessages();
            this.editingMessageId = null;
            this.renderMessages();

            if (window.showSuccess) {
                showSuccess('Сообщение обновлено');
            }

        } catch (error) {
            console.error('Ошибка сохранения сообщения:', error);
            if (window.showError) {
                showError('Ошибка сохранения сообщения');
            }
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
            const personId = getPersonIdFromUrl();
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
     * Показать пустое состояние
     */
    showEmptyState() {
        const container = document.getElementById('messagesList');
        if (!container) return;

        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">💬</div>
                <h3>Нет сообщений</h3>
                <p>Здесь будут отображаться сообщения и заметки</p>
            </div>
        `;
    }

    /**
     * Экранирование HTML
     */
    escapeHtml(unsafe) {
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
