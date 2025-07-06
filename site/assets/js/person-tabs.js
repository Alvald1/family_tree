// Управление табами на странице персоны
class PersonTabs {
    constructor() {
        this.activeTab = 'messages';
        this.tabs = new Map();
        this.init();
    }

    init() {
        this.setupTabs();
        this.bindEvents();
    }

    /**
     * Настройка табов
     */
    setupTabs() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(button => {
            const tabName = button.getAttribute('data-tab');
            const content = document.getElementById(`${tabName}-tab`);

            if (content) {
                this.tabs.set(tabName, {
                    button: button,
                    content: content,
                    loaded: false
                });
            }
        });
    }

    /**
     * Привязка событий
     */
    bindEvents() {
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const tabName = e.target.getAttribute('data-tab');
                this.switchTab(tabName);
            });
        });
    }

    /**
     * Переключение таба
     * @param {string} tabName - имя таба
     */
    switchTab(tabName) {
        if (!this.tabs.has(tabName) || this.activeTab === tabName) {
            return;
        }

        // Деактивируем текущий таб
        const currentTab = this.tabs.get(this.activeTab);
        if (currentTab) {
            currentTab.button.classList.remove('active');
            currentTab.content.classList.remove('active');
        }

        // Активируем новый таб
        const newTab = this.tabs.get(tabName);
        if (newTab) {
            newTab.button.classList.add('active');
            newTab.content.classList.add('active');

            this.activeTab = tabName;

            // Загружаем контент только при первом переключении на таб
            // НЕ загружаем автоматически при инициализации
            if (!newTab.loaded) {
                this.loadTabContent(tabName);
                newTab.loaded = true;
            }

            // Сохраняем активный таб в localStorage
            Utils.saveToLocalStorage('activePersonTab', tabName);

            // Уведомляем о смене таба
            this.onTabChange(tabName);
        }
    }

    /**
     * Загрузка контента таба
     * @param {string} tabName - имя таба
     */
    loadTabContent(tabName) {
        const personId = getPersonIdFromUrl();
        if (!personId) return;

        switch (tabName) {
            case 'messages':
                if (window.personMessages) {
                    window.personMessages.loadMessages(personId);
                }
                break;
            case 'photos':
                if (window.personPhotos) {
                    window.personPhotos.loadPhotos(personId);
                }
                break;
        }
    }

    /**
     * Восстановление активного таба из localStorage
     */
    restoreActiveTab() {
        const savedTab = Utils.loadFromLocalStorage('activePersonTab', 'messages');
        // Проверяем, что сохраненный таб все еще доступен
        const validTabs = ['messages', 'photos'];
        const tabToActivate = validTabs.includes(savedTab) ? savedTab : 'messages';

        if (this.tabs.has(tabToActivate)) {
            this.switchTab(tabToActivate);
        } else {
            // Если нет сохранённого таба или он недоступен, загружаем контент активного таба
            this.loadTabContent(this.activeTab);
            const currentTab = this.tabs.get(this.activeTab);
            if (currentTab) {
                currentTab.loaded = true;
            }
        }

        // Убедимся, что контент активного таба загружен
        const activeTab = this.tabs.get(this.activeTab);
        if (activeTab && !activeTab.loaded) {
            this.loadTabContent(this.activeTab);
            activeTab.loaded = true;
        }
    }

    /**
     * Получение активного таба
     * @returns {string} имя активного таба
     */
    getActiveTab() {
        return this.activeTab;
    }

    /**
     * Обработчик смены таба
     * @param {string} tabName - имя нового активного таба
     */
    onTabChange(tabName) {
        // Можно добавить дополнительную логику при смене табов

        // Отправляем кастомное событие
        const event = new CustomEvent('tabChange', {
            detail: { tabName, previousTab: this.activeTab }
        });
        document.dispatchEvent(event);
    }

    /**
     * Показ бейджа с количеством элементов на табе
     * @param {string} tabName - имя таба
     * @param {number} count - количество элементов
     */
    showTabBadge(tabName, count) {
        const tab = this.tabs.get(tabName);
        if (!tab) return;

        let badge = tab.button.querySelector('.tab-badge');
        if (!badge) {
            badge = Utils.createElement('span', { className: 'tab-badge' });
            tab.button.appendChild(badge);
        }

        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'inline';
        } else {
            badge.style.display = 'none';
        }
    }
}

// Добавляем стили для бейджей
const tabBadgeStyles = `
    .tab-badge {
        background: #f44336;
        color: white;
        border-radius: 10px;
        padding: 2px 6px;
        font-size: 11px;
        font-weight: bold;
        margin-left: 5px;
        min-width: 16px;
        text-align: center;
        display: none;
    }
`;

// Добавляем стили в head
const styleSheet = document.createElement('style');
styleSheet.textContent = tabBadgeStyles;
document.head.appendChild(styleSheet);

// Утилита для экранирования HTML
Utils.escapeHtml = function (text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
};

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PersonTabs;
}
