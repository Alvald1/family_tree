// Интерактивность для просмотрщика дерева
class TreeInteractions {
    constructor(treeViewer) {
        this.viewer = treeViewer;
        this.container = treeViewer.container;
        this.isDragging = false;
        this.dragStart = { x: 0, y: 0 };
        this.initialTranslate = { x: 0, y: 0 };

        this.init();
    }

    init() {
        this.setupMouseInteractions();
        this.setupTouchInteractions();
        this.setupKeyboardInteractions();
        this.setupViewControls();
    }

    /**
     * Настройка взаимодействий с мышью
     */
    setupMouseInteractions() {
        // Масштабирование колесом мыши
        this.container.addEventListener('wheel', (e) => {
            e.preventDefault();

            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            this.viewer.zoom(delta, e.clientX, e.clientY);
        });

        // Перетаскивание
        this.container.addEventListener('mousedown', (e) => {
            if (e.button === 0) { // Левая кнопка мыши
                this.startDrag(e.clientX, e.clientY);
                e.preventDefault();
            }
        });

        document.addEventListener('mousemove', Utils.throttle((e) => {
            if (this.isDragging) {
                this.updateDrag(e.clientX, e.clientY);
                e.preventDefault();
            }
        }, 16)); // ~60fps

        document.addEventListener('mouseup', () => {
            this.endDrag();
        });

        // Курсор
        this.container.addEventListener('mouseleave', () => {
            this.endDrag();
        });

        // Предотвращение контекстного меню
        this.container.addEventListener('contextmenu', (e) => {
            e.preventDefault();
        });
    }

    /**
     * Настройка сенсорных взаимодействий
     */
    setupTouchInteractions() {
        let initialDistance = 0;
        let initialZoom = 1;
        let lastTouchCenter = { x: 0, y: 0 };

        this.container.addEventListener('touchstart', (e) => {
            e.preventDefault();

            if (e.touches.length === 1) {
                // Одиночное касание - перетаскивание
                const touch = e.touches[0];
                this.startDrag(touch.clientX, touch.clientY);
            } else if (e.touches.length === 2) {
                // Двойное касание - масштабирование
                this.endDrag();

                const touch1 = e.touches[0];
                const touch2 = e.touches[1];

                initialDistance = this.getTouchDistance(touch1, touch2);
                initialZoom = this.viewer.currentZoom;
                lastTouchCenter = this.getTouchCenter(touch1, touch2);
            }
        });

        this.container.addEventListener('touchmove', Utils.throttle((e) => {
            e.preventDefault();

            if (e.touches.length === 1 && this.isDragging) {
                // Перетаскивание
                const touch = e.touches[0];
                this.updateDrag(touch.clientX, touch.clientY);
            } else if (e.touches.length === 2) {
                // Масштабирование
                const touch1 = e.touches[0];
                const touch2 = e.touches[1];

                const distance = this.getTouchDistance(touch1, touch2);
                const center = this.getTouchCenter(touch1, touch2);

                if (initialDistance > 0) {
                    const scale = distance / initialDistance;
                    const newZoom = Utils.clamp(
                        initialZoom * scale,
                        AppConfig.viewer.minZoom,
                        AppConfig.viewer.maxZoom
                    );

                    // Обновляем масштаб относительно центра касаний
                    this.viewer.currentZoom = newZoom;
                    this.viewer.updateTransform();
                }

                lastTouchCenter = center;
            }
        }, 16)); // ~60fps

        this.container.addEventListener('touchend', (e) => {
            if (e.touches.length === 0) {
                this.endDrag();
                initialDistance = 0;
                initialZoom = 1;
            } else if (e.touches.length === 1) {
                // Переход от масштабирования к перетаскиванию
                const touch = e.touches[0];
                this.startDrag(touch.clientX, touch.clientY);
                initialDistance = 0;
            }
        });
    }

    /**
     * Настройка клавиатурных взаимодействий
     */
    setupKeyboardInteractions() {
        document.addEventListener('keydown', (e) => {
            // Проверяем, что фокус на контейнере или его дочерних элементах
            if (!this.container.contains(document.activeElement) &&
                document.activeElement !== document.body) {
                return;
            }

            switch (e.key) {
                case 'ArrowUp':
                    this.viewer.translate(0, 50);
                    e.preventDefault();
                    break;
                case 'ArrowDown':
                    this.viewer.translate(0, -50);
                    e.preventDefault();
                    break;
                case 'ArrowLeft':
                    this.viewer.translate(50, 0);
                    e.preventDefault();
                    break;
                case 'ArrowRight':
                    this.viewer.translate(-50, 0);
                    e.preventDefault();
                    break;
                case '+':
                case '=':
                    this.viewer.zoom(1.1);
                    e.preventDefault();
                    break;
                case '-':
                    this.viewer.zoom(0.9);
                    e.preventDefault();
                    break;
                case '0':
                    this.viewer.resetView();
                    e.preventDefault();
                    break;
                case 'Home':
                    this.viewer.resetView();
                    e.preventDefault();
                    break;
            }
        });

        // Делаем контейнер фокусируемым для клавиатурного управления
        this.container.setAttribute('tabindex', '0');
        this.container.style.outline = 'none';
    }

    /**
     * Настройка элементов управления просмотром
     */
    setupViewControls() {
        const controlsContainer = Utils.createElement('div', {
            className: 'view-controls'
        });

        // Кнопка увеличения
        const zoomInBtn = this.createControlButton('+', 'Увеличить', () => {
            this.viewer.zoom(1.1);
        });

        // Кнопка уменьшения
        const zoomOutBtn = this.createControlButton('−', 'Уменьшить', () => {
            this.viewer.zoom(0.9);
        });

        // Кнопка сброса
        const resetBtn = this.createControlButton('⌂', 'Сбросить вид', () => {
            this.viewer.resetView();
        });

        // Кнопка полноэкранного режима
        const fullscreenBtn = this.createControlButton('⛶', 'Полный экран', () => {
            this.toggleFullscreen();
        });

        controlsContainer.appendChild(zoomInBtn);
        controlsContainer.appendChild(zoomOutBtn);
        controlsContainer.appendChild(resetBtn);
        controlsContainer.appendChild(fullscreenBtn);

        this.container.appendChild(controlsContainer);

        // Индикатор уровня масштабирования
        this.zoomIndicator = Utils.createElement('div', {
            className: 'zoom-level'
        });
        this.container.appendChild(this.zoomIndicator);
        this.updateZoomIndicator();
    }

    /**
     * Создание кнопки управления
     */
    createControlButton(text, title, onClick) {
        const button = Utils.createElement('button', {
            className: 'control-btn',
            type: 'button',
            title: title
        }, text);

        button.addEventListener('click', onClick);
        return button;
    }

    /**
     * Начало перетаскивания
     */
    startDrag(x, y) {
        this.isDragging = true;
        this.dragStart = { x, y };
        this.initialTranslate = {
            x: this.viewer.translateX,
            y: this.viewer.translateY
        };
        this.container.style.cursor = 'grabbing';
    }

    /**
     * Обновление перетаскивания
     */
    updateDrag(x, y) {
        if (!this.isDragging) return;

        const deltaX = x - this.dragStart.x;
        const deltaY = y - this.dragStart.y;

        this.viewer.translateX = this.initialTranslate.x + deltaX;
        this.viewer.translateY = this.initialTranslate.y + deltaY;
        this.viewer.updateTransform();
    }

    /**
     * Окончание перетаскивания
     */
    endDrag() {
        this.isDragging = false;
        this.container.style.cursor = 'grab';
    }

    /**
     * Расстояние между двумя касаниями
     */
    getTouchDistance(touch1, touch2) {
        const dx = touch1.clientX - touch2.clientX;
        const dy = touch1.clientY - touch2.clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }

    /**
     * Центр между двумя касаниями
     */
    getTouchCenter(touch1, touch2) {
        return {
            x: (touch1.clientX + touch2.clientX) / 2,
            y: (touch1.clientY + touch2.clientY) / 2
        };
    }

    /**
     * Переключение полноэкранного режима
     */
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            this.container.requestFullscreen().catch(err => {
                console.error(`Не удалось войти в полноэкранный режим: ${err.message}`);
            });
        } else {
            document.exitFullscreen();
        }
    }

    /**
     * Обновление индикатора масштабирования
     */
    updateZoomIndicator() {
        if (this.zoomIndicator) {
            const zoomPercent = Math.round(this.viewer.currentZoom * 100);
            this.zoomIndicator.textContent = `${zoomPercent}%`;
        }
    }

    /**
     * Подписка на изменения масштаба
     */
    onZoomChange() {
        this.updateZoomIndicator();
    }
}

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TreeInteractions;
}
