// Просмотрщик семейного дерева
class TreeViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.svg = null;
        this.currentZoom = AppConfig.viewer.defaultZoom;
        this.translateX = 0;
        this.translateY = 0;
        this.viewState = null;
        this.personContextMenu = null;
        this.handleDocumentClick = this.handleDocumentClick.bind(this);
        this.handleDocumentKeyDown = this.handleDocumentKeyDown.bind(this);

        if (!this.container) {
            throw new Error(`Container with ID "${containerId}" not found`);
        }

        this.ready = this.init();
    }

    init() {
        this.setupEventListeners();
        return this.loadSVG();
    }

    /**
     * Загрузка SVG файла
     */
    async loadSVG() {
        try {
            this.showLoading();

            const response = await Utils.fetchStatic(AppConfig.files.familyTreeSvg);
            const svgText = await response.text();

            this.container.innerHTML = svgText;
            this.svg = this.container.querySelector('svg');

            if (this.svg) {
                this.setupSVG();
                this.restoreViewState();
            } else {
                throw new Error('SVG element not found in loaded content');
            }

        } catch (error) {
            console.error('SVG loading error:', error);
            this.showError(error);
        }
    }

    /**
     * Настройка SVG элемента
     */
    setupSVG() {
        this.svg.setAttribute('width', '100%');
        this.svg.setAttribute('height', 'auto');
        this.svg.style.display = 'block';
        this.svg.style.transformOrigin = '0 0';

        this.addPersonClickHandlers();
        this.updateTransform();
    }

    /**
     * Показ индикатора загрузки
     */
    showLoading() {
        this.container.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p>${AppConfig.messages.loading}</p>
            </div>
        `;
    }

    /**
     * Показ ошибки загрузки
     */
    showError(error) {
        const errorDetails = error.message.includes('404') ?
            AppConfig.messages.fileNotFound :
            AppConfig.messages.networkError;

        this.container.innerHTML = `
            <div class="error-message">
                <h3>${AppConfig.icons.error} ${AppConfig.messages.loadError}</h3>
                <p><strong>${errorDetails}</strong></p>
                <p>Возможные решения:</p>
                <ul style="text-align: left; display: inline-block;">
                    <li>Запустите <code>python3 main.py</code> для создания дерева</li>
                    <li>Убедитесь, что файл source.txt содержит данные</li>
                    <li>Проверьте, что установлен Graphviz</li>
                </ul>
                <button class="btn js-reload">
                    🔄 Перезагрузить страницу
                </button>
            </div>
        `;
    }

    /**
     * Добавление обработчиков кликов на персон
     */
    addPersonClickHandlers() {
        const graphNodes = this.svg.querySelectorAll('g.node');

        // Используем делегирование событий вместо отдельных обработчиков для каждого узла
        this.svg.addEventListener('mouseenter', this.handleNodeMouseEnter.bind(this), true);
        this.svg.addEventListener('mouseleave', this.handleNodeMouseLeave.bind(this), true);
        this.svg.addEventListener('contextmenu', this.handleNodeContextMenu.bind(this));
        if (document.addEventListener) {
            document.addEventListener('click', this.handleDocumentClick);
            document.addEventListener('keydown', this.handleDocumentKeyDown);
        }

        // Добавляем только стили и тултипы для узлов
        graphNodes.forEach(node => {
            if (TreeViewer.getPersonIdFromNode(node)) {
                this.setupPersonNodeStyles(node);
            }
        });
    }

    static getPersonIdFromNode(node) {
        if (!node) return null;

        const title = node.querySelector ? node.querySelector('title') : null;
        const graphNodeId = title?.textContent?.trim();
        if (!graphNodeId || !/^\d+$/.test(graphNodeId)) {
            return null;
        }

        return `node${graphNodeId}`;
    }

    findPersonNode(target) {
        const node = target?.closest ? target.closest('g.node') : null;
        if (!TreeViewer.getPersonIdFromNode(node)) {
            return null;
        }
        return node;
    }

    /**
     * Обработчик входа мыши в узел
     */
    handleNodeMouseEnter(e) {
        const node = this.findPersonNode(e.target);
        if (node) {
            node.style.filter = 'drop-shadow(0 0 10px rgba(102, 126, 234, 0.6))';
            this.addNodeHighlight(node);
        }
    }

    /**
     * Обработчик выхода мыши из узла
     */
    handleNodeMouseLeave(e) {
        const node = this.findPersonNode(e.target);
        if (node) {
            node.style.filter = 'none';
            this.removeNodeHighlight(node);
        }
    }

    /**
     * Обработчик контекстного меню персоны
     */
    handleNodeContextMenu(e) {
        const node = this.findPersonNode(e.target);
        if (node) {
            e.preventDefault();
            e.stopPropagation();
            const personId = TreeViewer.getPersonIdFromNode(node);
            this.showPersonContextMenu(personId, e.clientX, e.clientY);
        }
    }

    /**
     * Показ меню действий для персоны
     */
    showPersonContextMenu(personId, clientX, clientY) {
        this.hidePersonContextMenu();

        const menu = Utils.createElement('div', {
            className: 'person-context-menu',
            role: 'menu'
        });
        const openProfileButton = Utils.createElement('button', {
            className: 'person-context-menu__item',
            type: 'button',
            role: 'menuitem'
        }, AppConfig.messages.openPersonProfile || 'Открыть профиль');

        openProfileButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.hidePersonContextMenu();
            this.openPersonPage(personId);
        });

        menu.appendChild(openProfileButton);
        this.container.appendChild(menu);
        this.personContextMenu = menu;
        this.positionPersonContextMenu(menu, clientX, clientY);
    }

    /**
     * Позиционирование меню рядом с курсором в пределах контейнера
     */
    positionPersonContextMenu(menu, clientX, clientY) {
        const rect = this.container.getBoundingClientRect();
        const padding = 8;
        const menuWidth = menu.offsetWidth || 160;
        const menuHeight = menu.offsetHeight || 44;
        const maxLeft = Math.max(padding, rect.width - menuWidth - padding);
        const maxTop = Math.max(padding, rect.height - menuHeight - padding);
        const left = Utils.clamp(clientX - rect.left, padding, maxLeft);
        const top = Utils.clamp(clientY - rect.top, padding, maxTop);

        menu.style.left = `${left}px`;
        menu.style.top = `${top}px`;
    }

    /**
     * Закрытие меню действий для персоны
     */
    hidePersonContextMenu() {
        if (this.personContextMenu) {
            this.personContextMenu.remove();
            this.personContextMenu = null;
        }
    }

    /**
     * Закрытие меню по клику вне него
     */
    handleDocumentClick(e) {
        if (this.personContextMenu && !this.personContextMenu.contains(e.target)) {
            this.hidePersonContextMenu();
        }
    }

    /**
     * Закрытие меню по Escape
     */
    handleDocumentKeyDown(e) {
        if (e.key === 'Escape') {
            this.hidePersonContextMenu();
        }
    }

    /**
     * Настройка стилей узла персоны
     */
    setupPersonNodeStyles(node) {
        // Стили для интерактивности
        node.style.cursor = 'pointer';
        node.style.transition = 'filter 0.2s ease';

        // Тултип
        this.addTooltip(node);
    }

    /**
     * Добавление подсветки узла
     */
    addNodeHighlight(node) {
        const textElements = node.querySelectorAll('text');
        const shapeElements = node.querySelectorAll('polygon, ellipse, rect');

        textElements.forEach(text => {
            text.style.fontWeight = 'bold';
        });

        shapeElements.forEach(shape => {
            shape.style.strokeWidth = '3';
        });
    }

    /**
     * Удаление подсветки узла
     */
    removeNodeHighlight(node) {
        const textElements = node.querySelectorAll('text');
        const shapeElements = node.querySelectorAll('polygon, ellipse, rect');

        textElements.forEach(text => {
            text.style.fontWeight = '';
        });

        shapeElements.forEach(shape => {
            shape.style.strokeWidth = '';
        });
    }

    /**
     * Добавление тултипа к узлу
     */
    addTooltip(node) {
        const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
        title.textContent = AppConfig.messages.personClickHint;
        node.appendChild(title);
    }

    /**
     * Открытие страницы персоны
     */
    openPersonPage(personId) {
        this.saveViewState();
        window.location.href = `person.html?id=${personId}`;
    }

    /**
     * Сохранение состояния просмотра
     */
    saveViewState() {
        if (!AppConfig.autoSave.enabled) return;

        const viewState = {
            zoom: this.currentZoom,
            translateX: this.translateX,
            translateY: this.translateY,
            timestamp: Date.now()
        };

        Utils.saveToLocalStorage(AppConfig.autoSave.localStorageKey, viewState);
    }

    /**
     * Восстановление состояния просмотра
     */
    restoreViewState() {
        if (!AppConfig.autoSave.enabled) return false;

        const savedState = Utils.loadFromLocalStorage(AppConfig.autoSave.localStorageKey);

        if (savedState && Utils.isTimestampValid(savedState.timestamp, AppConfig.viewer.stateExpirationTime)) {
            this.currentZoom = savedState.zoom || AppConfig.viewer.defaultZoom;
            this.translateX = savedState.translateX || 0;
            this.translateY = savedState.translateY || 0;
            this.updateTransform();
            return true;
        }

        return false;
    }

    /**
     * Обновление трансформации SVG
     */
    updateTransform() {
        if (!this.svg) return;

        this.svg.style.transform = `translate(${this.translateX}px, ${this.translateY}px) scale(${this.currentZoom})`;

        // Автосохранение с дебаунсом
        if (AppConfig.autoSave.enabled) {
            clearTimeout(this.saveTimeout);
            this.saveTimeout = setTimeout(() => {
                this.saveViewState();
            }, AppConfig.autoSave.debounceTime);
        }
    }

    /**
     * Масштабирование
     */
    zoom(delta, centerX, centerY) {
        const newZoom = Utils.clamp(
            this.currentZoom * delta,
            AppConfig.viewer.minZoom,
            AppConfig.viewer.maxZoom
        );

        if (centerX !== undefined && centerY !== undefined) {
            // Масштабирование относительно точки
            const rect = this.container.getBoundingClientRect();
            const containerPadding = 20;
            const mouseX = centerX - rect.left - containerPadding;
            const mouseY = centerY - rect.top - containerPadding;

            const pointBeforeX = (mouseX - this.translateX) / this.currentZoom;
            const pointBeforeY = (mouseY - this.translateY) / this.currentZoom;

            this.currentZoom = newZoom;
            this.translateX = mouseX - pointBeforeX * this.currentZoom;
            this.translateY = mouseY - pointBeforeY * this.currentZoom;
        } else {
            this.currentZoom = newZoom;
        }

        this.updateTransform();
    }

    /**
     * Перемещение
     */
    translate(deltaX, deltaY) {
        this.translateX += deltaX;
        this.translateY += deltaY;
        this.updateTransform();
    }

    /**
     * Сброс вида к начальному состоянию
     */
    resetView() {
        this.currentZoom = AppConfig.viewer.defaultZoom;
        this.translateX = 0;
        this.translateY = 0;
        this.updateTransform();
    }

    /**
     * Настройка обработчиков событий
     */
    setupEventListeners() {
        // Обработчики будут добавлены в tree-interactions.js
    }

    /**
     * Получение текущего состояния просмотра
     */
    getViewState() {
        return {
            zoom: this.currentZoom,
            translateX: this.translateX,
            translateY: this.translateY
        };
    }

    /**
     * Установка состояния просмотра
     */
    setViewState(state) {
        this.currentZoom = Utils.clamp(state.zoom || AppConfig.viewer.defaultZoom, AppConfig.viewer.minZoom, AppConfig.viewer.maxZoom);
        this.translateX = state.translateX || 0;
        this.translateY = state.translateY || 0;
        this.updateTransform();
    }
}

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TreeViewer;
}
