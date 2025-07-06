// Вспомогательные утилиты
const Utils = {
    /**
     * Дебаунс функции
     * @param {Function} func - функция для дебаунса
     * @param {number} wait - время ожидания в мс
     * @returns {Function} дебаунсированная функция
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Троттлинг функции
     * @param {Function} func - функция для троттлинга
     * @param {number} limit - лимит времени в мс
     * @returns {Function} троттлированная функция
     */
    throttle(func, limit) {
        let inThrottle;
        return function (...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * Получение параметра из URL
     * @param {string} param - имя параметра
     * @returns {string|null} значение параметра
     */
    getUrlParameter(param) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    },

    /**
     * Генерация уникального ID
     * @returns {string} уникальный идентификатор
     */
    generateId() {
        return 'id_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    },

    /**
     * Безопасный парсинг JSON
     * @param {string} jsonString - JSON строка
     * @param {*} defaultValue - значение по умолчанию
     * @returns {*} распарсенное значение или значение по умолчанию
     */
    safeJsonParse(jsonString, defaultValue = null) {
        try {
            return JSON.parse(jsonString);
        } catch (error) {
            console.warn('JSON parse error:', error);
            return defaultValue;
        }
    },

    /**
     * Форматирование даты
     * @param {Date|string|number} date - дата
     * @param {string} format - формат ('short', 'long', 'time')
     * @returns {string} отформатированная дата
     */
    formatDate(date, format = 'short') {
        if (!date) return '';

        const d = new Date(date);
        if (isNaN(d.getTime())) return '';

        const options = {
            short: { year: 'numeric', month: '2-digit', day: '2-digit' },
            long: {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                weekday: 'long'
            },
            time: {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            }
        };

        return d.toLocaleDateString('ru-RU', options[format] || options.short);
    },

    /**
     * Проверка поддержки localStorage
     * @returns {boolean} поддерживается ли localStorage
     */
    isLocalStorageAvailable() {
        try {
            const test = '__localStorage_test__';
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    },

    /**
     * Безопасное сохранение в localStorage
     * @param {string} key - ключ
     * @param {*} value - значение
     * @returns {boolean} успешность операции
     */
    saveToLocalStorage(key, value) {
        if (!this.isLocalStorageAvailable()) return false;

        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            return false;
        }
    },

    /**
     * Безопасное чтение из localStorage
     * @param {string} key - ключ
     * @param {*} defaultValue - значение по умолчанию
     * @returns {*} значение из localStorage или значение по умолчанию
     */
    loadFromLocalStorage(key, defaultValue = null) {
        if (!this.isLocalStorageAvailable()) return defaultValue;

        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            return defaultValue;
        }
    },

    /**
     * Проверка валидности временной метки
     * @param {number} timestamp - временная метка
     * @param {number} maxAge - максимальный возраст в мс
     * @returns {boolean} валидна ли временная метка
     */
    isTimestampValid(timestamp, maxAge) {
        return timestamp && (Date.now() - timestamp) < maxAge;
    },

    /**
     * Ограничение числа в диапазоне
     * @param {number} value - значение
     * @param {number} min - минимум
     * @param {number} max - максимум
     * @returns {number} ограниченное значение
     */
    clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    },

    /**
     * Проверка является ли элемент видимым
     * @param {HTMLElement} element - элемент
     * @returns {boolean} видим ли элемент
     */
    isElementVisible(element) {
        return element &&
            element.offsetWidth > 0 &&
            element.offsetHeight > 0 &&
            window.getComputedStyle(element).visibility !== 'hidden';
    },

    /**
     * Получение координат элемента относительно страницы
     * @param {HTMLElement} element - элемент
     * @returns {Object} координаты {x, y, width, height}
     */
    getElementBounds(element) {
        const rect = element.getBoundingClientRect();
        return {
            x: rect.left + window.pageXOffset,
            y: rect.top + window.pageYOffset,
            width: rect.width,
            height: rect.height
        };
    },

    /**
     * Загрузка файла с обработкой ошибок
     * @param {string} url - URL файла
     * @param {Object} options - опции запроса
     * @returns {Promise<Response>} промис с ответом
     */
    async fetchWithCache(url, options = {}) {
        const defaultOptions = {
            cache: 'no-cache',
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        };

        const timestamp = new Date().getTime();
        const urlWithTimestamp = url + (url.includes('?') ? '&' : '?') + `t=${timestamp}`;

        try {
            const response = await fetch(urlWithTimestamp, { ...defaultOptions, ...options });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return response;
        } catch (error) {
            throw error;
        }
    },

    /**
     * Создание элемента с атрибутами
     * @param {string} tagName - имя тега
     * @param {Object} attributes - атрибуты
     * @param {string} textContent - текстовое содержимое
     * @returns {HTMLElement} созданный элемент
     */
    createElement(tagName, attributes = {}, textContent = '') {
        const element = document.createElement(tagName);

        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'style' && typeof value === 'object') {
                Object.assign(element.style, value);
            } else {
                element.setAttribute(key, value);
            }
        });

        if (textContent) {
            element.textContent = textContent;
        }

        return element;
    },

    /**
     * Получение ID персоны из URL
     * @returns {string|null} ID персоны
     */
    getPersonIdFromUrl() {
        return this.getUrlParameter('id');
    },

};

// Глобальные функции для удобства использования
window.getPersonIdFromUrl = () => Utils.getPersonIdFromUrl();
window.escapeHtml = (unsafe) => {
    if (!unsafe) return '';
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
};

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Utils;
}
