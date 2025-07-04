// Главный файл приложения
class FamilyTreeApp {
    constructor() {
        this.treeViewer = null;
        this.interactions = null;
        this.isInitialized = false;
    }

    /**
     * Инициализация приложения
     */
    async init() {
        try {
            // Проверяем поддержку необходимых API
            this.checkBrowserSupport();

            // Инициализируем компоненты
            this.treeViewer = new TreeViewer('svgContainer');
            this.interactions = new TreeInteractions(this.treeViewer);

            // Подписываемся на события
            this.setupEventListeners();

            // Переопределяем метод обновления трансформации для синхронизации с индикатором масштаба
            const originalUpdateTransform = this.treeViewer.updateTransform.bind(this.treeViewer);
            this.treeViewer.updateTransform = () => {
                originalUpdateTransform();
                this.interactions.onZoomChange();
            };

            this.isInitialized = true;
            console.log('Family Tree App initialized successfully');

        } catch (error) {
            console.error('Failed to initialize Family Tree App:', error);
            notifications.error(`Ошибка инициализации приложения: ${error.message}`);
        }
    }

    /**
     * Проверка поддержки браузера
     */
    checkBrowserSupport() {
        const requiredFeatures = [
            'fetch',
            'Promise',
            'localStorage',
            'requestAnimationFrame'
        ];

        const missingFeatures = requiredFeatures.filter(feature =>
            !(feature in window) && !(feature in window.localStorage)
        );

        if (missingFeatures.length > 0) {
            throw new Error(`Браузер не поддерживает: ${missingFeatures.join(', ')}`);
        }

        // Проверяем поддержку SVG
        if (!document.createElementNS ||
            !document.createElementNS('http://www.w3.org/2000/svg', 'svg').createSVGRect) {
            throw new Error('Браузер не поддерживает SVG');
        }
    }

    /**
     * Настройка глобальных обработчиков событий
     */
    setupEventListeners() {
        // Обработка ошибок
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            notifications.error('Произошла непредвиденная ошибка');
        });

        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            notifications.error('Ошибка загрузки данных');
        });

        // Обработка изменения размера окна
        window.addEventListener('resize', Utils.debounce(() => {
            if (this.treeViewer && this.treeViewer.svg) {
                this.treeViewer.updateTransform();
            }
        }, 250));

        // Обработка видимости страницы
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible' && this.isInitialized) {
                // Страница стала видимой - можно обновить данные
                this.onPageVisible();
            }
        });

        // Обработка изменения ориентации устройства
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                if (this.treeViewer && this.treeViewer.svg) {
                    this.treeViewer.updateTransform();
                }
            }, 500);
        });
    }

    /**
     * Обработка становления страницы видимой
     */
    onPageVisible() {
        // Проверяем, нужно ли обновить дерево
        // Например, если файл мог измениться
        console.log('Page became visible, checking for updates...');
    }

    /**
     * Получение информации о состоянии приложения
     */
    getStatus() {
        return {
            initialized: this.isInitialized,
            hasTreeViewer: !!this.treeViewer,
            hasInteractions: !!this.interactions,
            currentZoom: this.treeViewer ? this.treeViewer.currentZoom : null,
            svgLoaded: this.treeViewer ? !!this.treeViewer.svg : false
        };
    }

    /**
     * Перезагрузка дерева
     */
    async reload() {
        if (!this.treeViewer) return;

        try {
            notifications.info('Перезагрузка дерева...');
            await this.treeViewer.loadSVG();
        } catch (error) {
            console.error('Reload failed:', error);
            notifications.error('Ошибка перезагрузки дерева');
        }
    }

    /**
     * Очистка ресурсов
     */
    destroy() {
        if (this.interactions) {
            // Здесь можно добавить очистку обработчиков событий
            this.interactions = null;
        }

        if (this.treeViewer) {
            this.treeViewer = null;
        }

        this.isInitialized = false;
    }
}

// Глобальный экземпляр приложения
let familyTreeApp = null;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', async () => {
    try {
        familyTreeApp = new FamilyTreeApp();
        await familyTreeApp.init();
    } catch (error) {
        console.error('Failed to start application:', error);
    }
});

// Глобальные функции для отладки и расширения
window.familyTree = {
    app: () => familyTreeApp,
    reload: () => familyTreeApp?.reload(),
    status: () => familyTreeApp?.getStatus(),
    zoom: (level) => familyTreeApp?.treeViewer?.setViewState({ zoom: level }),
    reset: () => familyTreeApp?.treeViewer?.resetView(),
    notifications: notifications
};

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { FamilyTreeApp, familyTreeApp };
}
