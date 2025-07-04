// API для работы с данными персон
class PersonAPI {
    constructor() {
        this.baseUrl = AppConfig.api.base;
    }

    /**
     * Получение информации о персоне
     * @param {string} personId - ID персоны
     * @returns {Promise<Object>} данные персоны
     */
    async getPersonInfo(personId) {
        try {
            const response = await Utils.fetchWithCache(`${this.baseUrl}/person/${personId}`);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error fetching person info:', error);

            // Fallback - возвращаем базовую информацию на основе ID
            return {
                id: personId,
                name: this.extractNameFromId(personId),
                dates: '',
                info: 'Информация недоступна'
            };
        }
    }

    /**
     * Получение сообщений персоны
     * @param {string} personId - ID персоны
     * @returns {Promise<Array>} список сообщений
     */
    async getPersonMessages(personId) {
        try {
            const response = await Utils.fetchWithCache(`${this.baseUrl}/person/${personId}/messages`);
            const data = await response.json();
            return data.messages || [];
        } catch (error) {
            console.error('Error fetching messages:', error);

            // Fallback - пытаемся загрузить из локального файла
            return await this.loadLocalMessages(personId);
        }
    }

    /**
     * Получение фотографий персоны
     * @param {string} personId - ID персоны
     * @returns {Promise<Array>} список фотографий
     */
    async getPersonPhotos(personId) {
        try {
            const response = await Utils.fetchWithCache(`${this.baseUrl}/person/${personId}/photos`);
            const data = await response.json();
            return data.photos || [];
        } catch (error) {
            console.error('Error fetching photos:', error);

            // Fallback - пытаемся загрузить из локального файла
            return await this.loadLocalPhotos(personId);
        }
    }

    /**
     * Получение записей блога персоны
     * @param {string} personId - ID персоны
     * @returns {Promise<Array>} список записей
     */
    async getPersonBlog(personId) {
        try {
            const response = await Utils.fetchWithCache(`${this.baseUrl}/person/${personId}/blog`);
            const data = await response.json();
            return data.posts || [];
        } catch (error) {
            console.error('Error fetching blog posts:', error);
            return [];
        }
    }

    /**
     * Добавление сообщения
     * @param {string} personId - ID персоны
     * @param {string} message - текст сообщения
     * @returns {Promise<Object>} результат операции
     */
    async addMessage(personId, message) {
        try {
            const response = await fetch(`${this.baseUrl}/person/${personId}/messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    timestamp: Date.now()
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error adding message:', error);
            throw error;
        }
    }

    /**
     * Обновление сообщения
     * @param {string} personId - ID персоны
     * @param {string} messageId - ID сообщения
     * @param {string} newMessage - новый текст сообщения
     * @returns {Promise<Object>} результат операции
     */
    async updateMessage(personId, messageId, newMessage) {
        try {
            const response = await fetch(`${this.baseUrl}/person/${personId}/messages/${messageId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: newMessage,
                    updated: Date.now()
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error updating message:', error);
            throw error;
        }
    }

    /**
     * Удаление сообщения
     * @param {string} personId - ID персоны
     * @param {string} messageId - ID сообщения
     * @returns {Promise<Object>} результат операции
     */
    async deleteMessage(personId, messageId) {
        try {
            const response = await fetch(`${this.baseUrl}/person/${personId}/messages/${messageId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error deleting message:', error);
            throw error;
        }
    }

    /**
     * Загрузка фотографии
     * @param {string} personId - ID персоны
     * @param {File} file - файл фотографии
     * @param {string} caption - описание фотографии
     * @returns {Promise<Object>} результат операции
     */
    async uploadPhoto(personId, file, caption = '') {
        try {
            const formData = new FormData();
            formData.append('photo', file);
            formData.append('caption', caption);
            formData.append('timestamp', Date.now().toString());

            const response = await fetch(`${this.baseUrl}/person/${personId}/photos`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error uploading photo:', error);
            throw error;
        }
    }

    /**
     * Удаление фотографии
     * @param {string} personId - ID персоны
     * @param {string} photoId - ID фотографии
     * @returns {Promise<Object>} результат операции
     */
    async deletePhoto(personId, photoId) {
        try {
            const response = await fetch(`${this.baseUrl}/person/${personId}/photos/${photoId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error deleting photo:', error);
            throw error;
        }
    }

    /**
     * Загрузка локальных сообщений (fallback)
     * @param {string} personId - ID персоны
     * @returns {Promise<Array>} список сообщений
     */
    async loadLocalMessages(personId) {
        try {
            const response = await Utils.fetchWithCache(`person_data/messages/${personId}.json`);
            const data = await response.json();
            return data.messages || [];
        } catch (error) {
            console.warn('No local messages found for person:', personId);
            return [];
        }
    }

    /**
     * Загрузка локальных фотографий (fallback)
     * @param {string} personId - ID персоны
     * @returns {Promise<Array>} список фотографий
     */
    async loadLocalPhotos(personId) {
        try {
            const response = await Utils.fetchWithCache(`person_data/photos/${personId}.json`);
            const data = await response.json();

            // Преобразуем относительные пути в абсолютные
            const photos = data.photos || [];
            return photos.map(photo => ({
                ...photo,
                url: photo.url.startsWith('http') ? photo.url : `person_data/photos/${photo.url}`
            }));
        } catch (error) {
            console.warn('No local photos found for person:', personId);
            return [];
        }
    }

    /**
     * Извлечение имени из ID (для fallback)
     * @param {string} personId - ID персоны
     * @returns {string} имя персоны
     */
    extractNameFromId(personId) {
        // Удаляем префикс "node" если есть
        let name = personId.replace(/^node/, '');

        // Преобразуем в читаемый вид
        name = name.replace(/([A-Z])/g, ' $1').trim();
        name = name.charAt(0).toUpperCase() + name.slice(1);

        return name || 'Неизвестная персона';
    }

    /**
     * Проверка доступности API
     * @returns {Promise<boolean>} доступность API
     */
    async checkAPIAvailability() {
        try {
            const response = await fetch(`${this.baseUrl}/health`, {
                method: 'HEAD',
                cache: 'no-cache'
            });
            return response.ok;
        } catch (error) {
            return false;
        }
    }
}

// Создаем глобальный экземпляр API
const personAPI = new PersonAPI();

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PersonAPI, personAPI };
}
