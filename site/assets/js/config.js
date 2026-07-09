// Конфигурация приложения
const AppConfig = {
    // API endpoints
    api: {
        base: '/api',
        person: '/api/person',
        photos: '/photos',
        messages: '/messages',
        blog: '/blog'
    },

    // Файлы данных
    files: {
        familyTreeSvg: 'family_tree_vector.svg',
        personDataDir: 'person_data'
    },

    // Настройки просмотрщика дерева
    viewer: {
        minZoom: 0.1,
        maxZoom: 5,
        zoomStep: 0.1,
        wheelZoomSensitivity: 0.0012,
        wheelZoomMaxStep: 0.04,
        defaultZoom: 1,
        saveStateEnabled: true,
        stateExpirationTime: 60 * 60 * 1000 // 1 час
    },

    // Настройки автосохранения
    autoSave: {
        enabled: true,
        debounceTime: 500,
        localStorageKey: 'treeViewState'
    },

    // Текстовые константы
    messages: {
        loading: 'Загрузка генеалогического дерева...',
        loadSuccess: 'Генеалогическое дерево загружено! Правый клик по персоне открывает меню действий.',
        loadError: 'Ошибка загрузки дерева',
        stateRestored: 'Состояние просмотра восстановлено',
        personPageOpening: 'Открываем страницу персоны...',
        fileNotFound: 'Файл family_tree_vector.svg не найден или поврежден.',
        networkError: 'Ошибка сети при загрузке дерева',
        personClickHint: 'Правый клик для открытия меню персоны',
        openPersonProfile: 'Открыть профиль'
    },

    // Иконки для уведомлений
    icons: {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️',
        loading: '⏳'
    },

    // Классы CSS
    cssClasses: {
        loading: 'svg-loading',
        error: 'error-message',
        hidden: 'hidden',
        dragging: 'dragging',
        highlight: 'node-highlight'
    }
};

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AppConfig;
}
