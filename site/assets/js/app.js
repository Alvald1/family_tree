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

        } catch (error) {
            // Ошибка инициализации
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
            // Обработка критических ошибок
        });

        window.addEventListener('unhandledrejection', (event) => {
            // Обработка необработанных промисов
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
    }

    /**
     * Перезагрузка дерева
     */
    async reload() {
        if (!this.treeViewer) return;

        try {
            await this.treeViewer.loadSVG();
        } catch (error) {
            // Ошибка перезагрузки
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
        // Ошибка запуска приложения
    }
});

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { FamilyTreeApp, familyTreeApp };
}
