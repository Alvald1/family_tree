// Главный файл страницы персоны
class PersonPage {
    constructor() {
        this.personId = null;
        this.personData = null;
        this.tabs = null;
        this.isInitialized = false;
    }

    /**
     * Инициализация страницы
     */
    async init() {
        try {
            // Получаем ID персоны из URL
            this.personId = getPersonIdFromUrl();

            if (!this.personId) {
                this.showError('ID персоны не указан');
                return;
            }

            // Инициализируем компоненты
            this.tabs = new PersonTabs();

            // Создаем глобальные объекты для управления сообщениями и фотографиями
            if (typeof PersonMessages !== 'undefined') {
                window.personMessages = new PersonMessages();
            }
            if (typeof PersonPhotos !== 'undefined') {
                window.personPhotos = new PersonPhotos();
            }

            // Загружаем основную информацию
            await this.loadPersonData();

            // Восстанавливаем активный таб
            this.tabs.restoreActiveTab();

            // Настраиваем обработчики событий
            this.setupEventListeners();

            this.isInitialized = true;

        } catch (error) {
            this.showError('Ошибка инициализации страницы');
        }
    }

    /**
     * Загрузка данных персоны
     */
    async loadPersonData() {
        try {
            // Показываем индикаторы загрузки
            this.showLoadingState();

            // Загружаем основную информацию
            this.personData = await personAPI.getPersonInfo(this.personId);

            // Обновляем заголовок страницы
            this.updatePageHeader();

            // Примечание: контент табов загружается через restoreActiveTab()

        } catch (error) {
            this.showError('Ошибка загрузки данных персоны');
        }
    }

    /**
     * Показ состояния загрузки
     */
    showLoadingState() {
        const nameElement = document.getElementById('personName');
        const datesElement = document.getElementById('personDates');

        if (nameElement) {
            nameElement.textContent = 'Загрузка...';
        }

        if (datesElement) {
            datesElement.textContent = '';
        }
    }

    /**
     * Обновление заголовка страницы
     */
    updatePageHeader() {
        if (!this.personData) {
            return;
        }

        const nameElement = document.getElementById('personName');
        const datesElement = document.getElementById('personDates');
        const detailsElement = document.getElementById('personDetails');

        if (nameElement) {
            const displayName = this.personData.name || 'Неизвестная персона';
            nameElement.textContent = displayName;
        }

        if (datesElement) {
            const displayDates = this.personData.dates || '';
            datesElement.textContent = displayDates;
        }

        // Загрузка дополнительной информации в секцию details
        if (detailsElement) {
            this.loadPersonDetails(detailsElement);
        }

        // Обновляем заголовок документа
        document.title = `${this.personData.name || 'Персона'} - Семейное дерево`;
    }

    /**
     * Загрузка дополнительной информации о персоне
     */
    loadPersonDetails(detailsElement) {
        const info = this.personData;
        let detailsHTML = '';

        // Основная информация
        if (info.full_info && info.full_info !== info.name) {
            detailsHTML += `<div class="person-info-item">${Utils.escapeHtml(info.full_info)}</div>`;
        }

        // ID персоны (используем правильный ID из URL, а не из API ответа)
        if (this.personId) {
            detailsHTML += `<div class="person-info-item"><strong>ID:</strong> ${Utils.escapeHtml(this.personId)}</div>`;
        }

        if (detailsHTML) {
            detailsElement.innerHTML = detailsHTML;
        } else {
            detailsElement.innerHTML = '<div class="person-info-item">Дополнительная информация отсутствует</div>';
        }
    }

    /**
     * Настройка обработчиков событий
     */
    setupEventListeners() {
        // Обработка ошибок
        window.addEventListener('error', (event) => {
            // Обработка критических ошибок
        });

        // Обработка смены табов
        document.addEventListener('tabChange', (event) => {
            // Можно добавить логику отслеживания активности
        });

        // Обработка изменения URL (если пользователь нажал назад/вперед)
        window.addEventListener('popstate', (event) => {
            const newPersonId = Utils.getUrlParameter('id');
            if (newPersonId !== this.personId) {
                this.personId = newPersonId;
                this.loadPersonData();
            }
        });

        // Обработка видимости страницы
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible' && this.isInitialized) {
                this.onPageVisible();
            }
        });

        // Горячие клавиши
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });

        // Обработка drag and drop файлов на всю страницу
        this.setupPageDragAndDrop();
    }

    /**
     * Настройка drag and drop для всей страницы
     */
    setupPageDragAndDrop() {
        let dragCounter = 0;

        document.addEventListener('dragenter', (e) => {
            e.preventDefault();
            dragCounter++;

            // Показываем overlay только для файлов и не в режиме сортировки
            if (e.dataTransfer.types.includes('Files') &&
                !(window.personPhotos && window.personPhotos.sortMode)) {
                this.showDropOverlay();
            }
        });

        document.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dragCounter--;

            if (dragCounter === 0) {
                this.hideDropOverlay();
            }
        });

        document.addEventListener('dragover', (e) => {
            e.preventDefault();
        });

        document.addEventListener('drop', (e) => {
            e.preventDefault();
            dragCounter = 0;
            this.hideDropOverlay();

            // Не обрабатываем файлы если в режиме сортировки фотографий
            if (window.personPhotos && window.personPhotos.sortMode) {
                return;
            }

            // Переключаемся на таб фотографий и обрабатываем файлы
            if (e.dataTransfer.files.length > 0) {
                this.tabs.switchTab('photos');
                setTimeout(() => {
                    if (window.personPhotos) {
                        window.personPhotos.handleFiles(e.dataTransfer.files);
                    }
                }, 300);
            }
        });
    }

    /**
     * Показ overlay для drag and drop
     */
    showDropOverlay() {
        // Не показываем overlay если в режиме сортировки фотографий
        if (window.personPhotos && window.personPhotos.sortMode) {
            return;
        }

        let overlay = document.querySelector('.page-drop-overlay');

        if (!overlay) {
            overlay = Utils.createElement('div', {
                className: 'page-drop-overlay',
                style: {
                    position: 'fixed',
                    top: '0',
                    left: '0',
                    right: '0',
                    bottom: '0',
                    background: 'rgba(102, 126, 234, 0.8)',
                    color: 'white',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: '10000',
                    backdropFilter: 'blur(5px)'
                }
            });

            overlay.innerHTML = `
                <div style="font-size: 64px; margin-bottom: 20px;">📷</div>
                <div style="font-size: 24px; font-weight: 500; margin-bottom: 10px;">Перетащите фотографии сюда</div>
                <div style="font-size: 16px; opacity: 0.8;">Они будут добавлены в фотоальбом персоны</div>
            `;

            document.body.appendChild(overlay);
        }

        overlay.style.display = 'flex';
    }

    /**
     * Скрытие overlay для drag and drop
     */
    hideDropOverlay() {
        const overlay = document.querySelector('.page-drop-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    /**
     * Обработка горячих клавиш
     * @param {KeyboardEvent} e - событие клавиатуры
     */
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + 1-4 для переключения табов
        if ((e.ctrlKey || e.metaKey) && e.key >= '1' && e.key <= '4') {
            e.preventDefault();

            const tabMap = {
                '1': 'messages',
                '2': 'photos',
                '3': 'blog',
                '4': 'info'
            };

            const tabName = tabMap[e.key];
            if (tabName) {
                this.tabs.switchTab(tabName);
            }
        }

        // Ctrl/Cmd + N для добавления нового элемента в активном табе
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();

            const activeTab = this.tabs.getActiveTab();
            switch (activeTab) {
                case 'messages':
                    if (window.personMessages) {
                        window.personMessages.showAddMessageModal();
                    }
                    break;
                case 'photos':
                    if (window.personPhotos) {
                        window.personPhotos.showAddPhotoModal();
                    }
                    break;
            }
        }

        // Escape для закрытия модальных окон
        if (e.key === 'Escape') {
            const modal = document.getElementById('modal-overlay');
            if (modal && !modal.classList.contains('hidden')) {
                if (window.personMessages) {
                    window.personMessages.hideModal();
                }
                if (window.personPhotos) {
                    window.personPhotos.hideModal();
                }
            }
        }
    }

    /**
     * Обработка становления страницы видимой
     */
    onPageVisible() {
        // Можно добавить логику обновления данных
    }

    /**
     * Показ ошибки
     * @param {string} message - сообщение об ошибке
     */
    showError(message) {
        const container = document.querySelector('.container');
        if (container) {
            container.innerHTML = `
                <div class="error-message" style="margin: 40px; text-align: center;">
                    <h2>❌ Ошибка</h2>
                    <p>${Utils.escapeHtml(message)}</p>
                    <div style="margin-top: 20px;">
                        <a href="index.html" class="btn">← Вернуться к дереву</a>
                        <button onclick="location.reload()" class="btn btn-secondary" style="margin-left: 10px;">🔄 Обновить</button>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Получение данных персоны
     * @returns {Object|null} данные персоны
     */
    getPersonData() {
        return this.personData;
    }

    /**
     * Получение ID персоны
     * @returns {string|null} ID персоны
     */
    getPersonId() {
        return this.personId;
    }

    /**
     * Получение статуса инициализации
     * @returns {boolean} инициализирована ли страница
     */
    isReady() {
        return this.isInitialized;
    }

    /**
     * Обновление данных персоны
     */
    async refresh() {
        if (!this.personId) return;

        try {
            await this.loadPersonData();
        } catch (error) {
            // Ошибка обновления данных
        }
    }

    /**
     * Переход к другой персоне
     * @param {string} newPersonId - ID новой персоны
     */
    navigateToSPerson(newPersonId) {
        if (newPersonId === this.personId) return;

        // Обновляем URL без перезагрузки страницы
        const newUrl = `person.html?id=${newPersonId}`;
        window.history.pushState({ personId: newPersonId }, '', newUrl);

        // Загружаем данные новой персоны
        this.personId = newPersonId;
        this.loadPersonData();
    }
}

// Глобальный экземпляр страницы персоны
let personPage = null;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Проверяем, было ли ФИО уже обновлено простым скриптом
        const nameElement = document.getElementById('personName');
        if (nameElement && nameElement.textContent !== 'Загрузка...') {
            // Инициализируем только табы и функциональность
            personPage = new PersonPage();
            personPage.personId = getPersonIdFromUrl();
            personPage.tabs = new PersonTabs();

            // Создаем глобальные объекты для управления сообщениями и фотографиями
            if (typeof PersonMessages !== 'undefined') {
                window.personMessages = new PersonMessages();
            }
            if (typeof PersonPhotos !== 'undefined') {
                window.personPhotos = new PersonPhotos();
            }

            // Восстанавливаем активный таб
            personPage.tabs.restoreActiveTab();
            personPage.setupEventListeners();
            personPage.isInitialized = true;
            return;
        }

        // Если ФИО не обновлено, запускаем полную инициализацию
        personPage = new PersonPage();
        await personPage.init();
    } catch (error) {
        console.error('Failed to start person page:', error);
    }
});

// Глобальные функции для отладки
window.personPage = {
    instance: () => personPage,
    refresh: () => personPage?.refresh(),
    data: () => personPage?.getPersonData(),
    navigateTo: (id) => personPage?.navigateToSPerson(id)
};

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PersonPage, personPage };
}
