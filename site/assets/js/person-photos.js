// Управление фотографиями персоны с возможностью изменения порядка
class PersonPhotos {
    constructor() {
        this.photos = [];
        this.sortMode = false;
        this.draggedIndex = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.setupDragAndDrop();
        this.setupSortMode();
    }

    /**
     * Привязка событий
     */
    bindEvents() {
        // Кнопка добавления фото
        const addBtn = document.getElementById('addPhotoBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => {
                this.addPhotoSimple();
            });
        }
    }

    /**
     * Простое добавление фото через input file
     */
    addPhotoSimple() {
        // Создаем временный input для выбора файла
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.multiple = true;

        input.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            if (files.length > 0) {
                this.uploadPhotos(files);
            }
        });

        input.click();
    }

    /**
     * Загрузка фотографий
     */
    async uploadPhotos(files) {
        try {
            const personId = getPersonIdFromUrl();

            for (const file of files) {
                if (!file.type.startsWith('image/')) {
                    console.warn('Пропускаем файл, не являющийся изображением:', file.name);
                    continue;
                }

                const formData = new FormData();
                formData.append('photo', file);

                const response = await fetch(`/api/person/${personId}/photos`, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error(`Ошибка загрузки ${file.name}`);
                }

                const result = await response.json();
                if (result.success && result.photo) {
                    this.photos.unshift(result.photo);
                }
            }

            this.renderPhotos();

            if (window.showSuccess) {
                showSuccess(`Загружено фотографий: ${files.length}`);
            }

        } catch (error) {
            console.error('Ошибка загрузки фотографий:', error);
            if (window.showError) {
                showError('Ошибка загрузки фотографий');
            }
        }
    }

    /**
     * Настройка drag & drop для загрузки файлов
     */
    setupDragAndDrop() {
        const photosGrid = document.getElementById('photosGrid');
        if (!photosGrid) return;

        // Создаем обработчики как методы класса для возможности их удаления
        this.handleDragEnter = (e) => {
            if (this.sortMode) return;
            this.preventDefaults(e);
            photosGrid.classList.add('drag-over');
        };

        this.handleDragOver = (e) => {
            if (this.sortMode) return;
            this.preventDefaults(e);
        };

        this.handleDragLeave = (e) => {
            if (this.sortMode) return;
            this.preventDefaults(e);
            photosGrid.classList.remove('drag-over');
        };

        this.handleDrop = (e) => {
            if (this.sortMode) return;
            this.preventDefaults(e);
            photosGrid.classList.remove('drag-over');

            const files = Array.from(e.dataTransfer.files);
            const imageFiles = files.filter(file => file.type.startsWith('image/'));

            if (imageFiles.length > 0) {
                this.uploadPhotos(imageFiles);
            }
        };

        // Изначально включаем drag-and-drop
        this.enableDragAndDrop();
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    /**
     * Настройка режима сортировки
     */
    setupSortMode() {
        // Добавляем кнопку переключения режима сортировки
        const photosHeader = document.querySelector('.photos-header');
        if (photosHeader) {
            const sortToggle = document.createElement('button');
            sortToggle.className = 'sort-mode-toggle';
            sortToggle.id = 'sortModeToggle';
            sortToggle.innerHTML = '🔄 Изменить порядок';
            sortToggle.title = 'Включить/выключить режим изменения порядка фотографий';

            sortToggle.addEventListener('click', () => {
                this.toggleSortMode();
            });

            photosHeader.appendChild(sortToggle);
        }

        // Добавляем инструкции
        const photosContainer = document.querySelector('.photos-container');
        if (photosContainer) {
            const instructions = document.createElement('div');
            instructions.className = 'sort-instructions';
            instructions.id = 'sortInstructions';
            instructions.innerHTML = `
                <span class="icon">👆</span>
                Перетаскивайте фотографии для изменения их порядка. Нажмите "Сохранить порядок" для применения изменений.
            `;

            photosContainer.insertBefore(instructions, photosContainer.querySelector('.photos-grid'));
        }
    }

    /**
     * Переключение режима сортировки
     */
    toggleSortMode() {
        this.sortMode = !this.sortMode;
        const grid = document.getElementById('photosGrid');
        const toggle = document.getElementById('sortModeToggle');
        const instructions = document.getElementById('sortInstructions');

        if (this.sortMode) {
            grid?.classList.add('sortable');
            toggle?.classList.add('active');
            toggle.innerHTML = '💾 Сохранить порядок';
            instructions?.classList.add('visible');
            // Отключаем drag-and-drop для загрузки файлов
            this.disableDragAndDrop();
            // Обновляем отображение для режима сортировки
            this.renderPhotos();
        } else {
            grid?.classList.remove('sortable');
            toggle?.classList.remove('active');
            toggle.innerHTML = '🔄 Изменить порядок';
            instructions?.classList.remove('visible');
            // Очищаем обработчики сортировки
            this.clearPhotoSorting();
            // Сохраняем порядок только если есть фотографии
            if (this.photos.length > 0) {
                this.savePhotoOrder();
            }
            // Включаем обратно drag-and-drop для загрузки файлов
            this.enableDragAndDrop();
            // Обновляем отображение для обычного режима
            this.renderPhotos();
        }
    }

    /**
     * Отключение drag-and-drop для загрузки файлов
     */
    disableDragAndDrop() {
        const photosGrid = document.getElementById('photosGrid');
        if (!photosGrid) return;

        photosGrid.removeEventListener('dragenter', this.handleDragEnter, false);
        photosGrid.removeEventListener('dragover', this.handleDragOver, false);
        photosGrid.removeEventListener('dragleave', this.handleDragLeave, false);
        photosGrid.removeEventListener('drop', this.handleDrop, false);

        // Убираем все классы связанные с drag-and-drop
        photosGrid.classList.remove('drag-over');
    }

    /**
     * Включение drag-and-drop для загрузки файлов
     */
    enableDragAndDrop() {
        const photosGrid = document.getElementById('photosGrid');
        if (!photosGrid) return;

        photosGrid.addEventListener('dragenter', this.handleDragEnter, false);
        photosGrid.addEventListener('dragover', this.handleDragOver, false);
        photosGrid.addEventListener('dragleave', this.handleDragLeave, false);
        photosGrid.addEventListener('drop', this.handleDrop, false);
    }

    /**
     * Настройка сортировки фотографий
     */
    setupPhotoSorting() {
        const grid = document.getElementById('photosGrid');
        if (!grid) return;

        grid.querySelectorAll('.photo-item').forEach((item, index) => {
            item.draggable = true;
            item.dataset.originalIndex = index;

            // Удаляем старые обработчики если они есть
            item.removeEventListener('dragstart', item._dragStartHandler);
            item.removeEventListener('dragend', item._dragEndHandler);
            item.removeEventListener('dragover', item._dragOverHandler);
            item.removeEventListener('dragenter', item._dragEnterHandler);
            item.removeEventListener('dragleave', item._dragLeaveHandler);
            item.removeEventListener('drop', item._dropHandler);

            // Создаем новые обработчики
            item._dragStartHandler = (e) => {
                this.draggedIndex = parseInt(e.target.closest('.photo-item').dataset.index);
                e.target.closest('.photo-item').classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/html', e.target.outerHTML);
            };

            item._dragEndHandler = (e) => {
                e.target.closest('.photo-item').classList.remove('dragging');
                grid.querySelectorAll('.photo-item').forEach(i => {
                    i.classList.remove('drag-over');
                });
            };

            item._dragOverHandler = (e) => {
                e.preventDefault();
                e.stopPropagation();
                e.dataTransfer.dropEffect = 'move';
            };

            item._dragEnterHandler = (e) => {
                e.preventDefault();
                e.stopPropagation();
                const photoItem = e.target.closest('.photo-item');
                if (photoItem && photoItem !== document.querySelector('.photo-item.dragging')) {
                    photoItem.classList.add('drag-over');
                }
            };

            item._dragLeaveHandler = (e) => {
                const photoItem = e.target.closest('.photo-item');
                if (photoItem && !photoItem.contains(e.relatedTarget)) {
                    photoItem.classList.remove('drag-over');
                }
            };

            item._dropHandler = (e) => {
                e.preventDefault();
                e.stopPropagation();

                const photoItem = e.target.closest('.photo-item');
                if (photoItem) {
                    photoItem.classList.remove('drag-over');

                    const dropIndex = parseInt(photoItem.dataset.index);
                    if (this.draggedIndex !== null && this.draggedIndex !== dropIndex) {
                        this.movePhoto(this.draggedIndex, dropIndex);
                    }
                }
                this.draggedIndex = null;
            };

            // Добавляем обработчики
            item.addEventListener('dragstart', item._dragStartHandler);
            item.addEventListener('dragend', item._dragEndHandler);
            item.addEventListener('dragover', item._dragOverHandler);
            item.addEventListener('dragenter', item._dragEnterHandler);
            item.addEventListener('dragleave', item._dragLeaveHandler);
            item.addEventListener('drop', item._dropHandler);
        });
    }

    /**
     * Обработка файлов (вызывается из глобального drag-and-drop)
     */
    handleFiles(files) {
        const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
        if (imageFiles.length > 0) {
            this.uploadPhotos(imageFiles);
        }
    }

    /**
     * Очистка обработчиков сортировки
     */
    clearPhotoSorting() {
        const grid = document.getElementById('photosGrid');
        if (!grid) return;

        grid.querySelectorAll('.photo-item').forEach(item => {
            item.draggable = false;
            item.removeEventListener('dragstart', item._dragStartHandler);
            item.removeEventListener('dragend', item._dragEndHandler);
            item.removeEventListener('dragover', item._dragOverHandler);
            item.removeEventListener('dragenter', item._dragEnterHandler);
            item.removeEventListener('dragleave', item._dragLeaveHandler);
            item.removeEventListener('drop', item._dropHandler);

            // Удаляем все классы связанные с перетаскиванием
            item.classList.remove('dragging', 'drag-over');
        });
    }

    /**
     * Перемещение фотографии в массиве
     */
    movePhoto(fromIndex, toIndex) {
        if (fromIndex === toIndex) return;

        const photo = this.photos.splice(fromIndex, 1)[0];
        this.photos.splice(toIndex, 0, photo);

        this.renderPhotos();
        if (this.sortMode) {
            this.setupPhotoSorting();
        }
    }

    /**
     * Сохранение нового порядка фотографий
     */
    async savePhotoOrder() {
        try {
            const personId = getPersonIdFromUrl();
            // Создаем массив с новым порядком - просто последовательность от 0 до длины массива
            // так как фотографии уже переупорядочены в this.photos
            const order = Array.from({ length: this.photos.length }, (_, i) => i);

            const response = await fetch(`/api/person/${personId}/photos/reorder`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ order, photos: this.photos })
            });

            if (!response.ok) {
                throw new Error('Ошибка сохранения порядка фотографий');
            }

            const result = await response.json();
            if (result.success) {
                this.photos = result.photos;
                if (window.showSuccess) {
                    showSuccess('Порядок фотографий сохранен');
                }
            }

        } catch (error) {
            console.error('Ошибка сохранения порядка фотографий:', error);
            if (window.showError) {
                showError('Ошибка сохранения порядка фотографий');
            }
        }
    }

    /**
     * Загрузка фотографий с сервера
     */
    async loadPhotos(personId) {
        try {
            const photosGrid = document.getElementById('photosGrid');
            if (!photosGrid) return;

            // Показываем индикатор загрузки
            photosGrid.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Загрузка фотографий...</p>
                </div>
            `;

            const response = await fetch(`/api/person/${personId}/photos`);
            if (!response.ok) {
                throw new Error('Ошибка загрузки фотографий');
            }

            this.photos = await response.json();
            this.renderPhotos();

        } catch (error) {
            console.error('Ошибка загрузки фотографий:', error);
            const photosGrid = document.getElementById('photosGrid');
            if (photosGrid) {
                photosGrid.innerHTML = `
                    <div class="error-message">
                        <h3>Ошибка загрузки фотографий</h3>
                        <p>Не удалось загрузить фотографии. Попробуйте обновить страницу.</p>
                        <button onclick="window.location.reload()" class="btn">Обновить</button>
                    </div>
                `;
            }
        }
    }

    /**
     * Отображение фотографий
     */
    renderPhotos() {
        const container = document.getElementById('photosGrid');
        if (!container) return;

        if (this.photos.length === 0) {
            this.showEmptyState();
            return;
        }

        const photosHTML = this.photos.map((photo, index) =>
            this.createPhotoHTML(photo, index)
        ).join('');

        container.innerHTML = photosHTML;
        this.bindPhotoEvents();

        // Если режим сортировки включен, настраиваем перетаскивание
        if (this.sortMode) {
            this.setupPhotoSorting();
        }
    }

    /**
     * Создание HTML для фотографии
     */
    createPhotoHTML(photo, index) {
        const sortHandle = this.sortMode ?
            `<button class="btn btn-sm photo-action-btn photo-sort-handle" title="Перетащить">⚫</button>` : '';

        return `
            <div class="photo-item" data-index="${index}">
                <div class="photo-wrapper">
                    <img class="photo-image" src="${photo.url}" alt="${this.escapeHtml(photo.caption || 'Фото')}" 
                         loading="lazy" onclick="window.personPhotos.viewPhoto(${index})">
                    <div class="photo-overlay">
                        <div class="photo-actions">
                            ${sortHandle}
                            <button class="btn btn-sm photo-action-btn photo-view" data-index="${index}" title="Просмотр">👁</button>
                            <button class="btn btn-sm photo-action-btn btn-danger photo-delete" data-index="${index}" title="Удалить">✕</button>
                        </div>
                    </div>
                </div>
                <div class="photo-info">
                    ${photo.caption ? `<p class="photo-caption">${this.escapeHtml(photo.caption)}</p>` : ''}
                    ${photo.date ? `<span class="photo-date">${new Date(photo.date).toLocaleDateString('ru-RU')}</span>` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Привязка событий к фотографиям
     */
    bindPhotoEvents() {
        const container = document.getElementById('photosGrid');
        if (!container) return;

        // Просмотр фото
        container.querySelectorAll('.photo-view').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const index = parseInt(e.target.dataset.index);
                this.viewPhoto(index);
            });
        });

        // Удаление фото
        container.querySelectorAll('.photo-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const index = parseInt(e.target.dataset.index);
                this.deletePhoto(index);
            });
        });
    }

    /**
     * Просмотр фотографии в новом окне
     */
    viewPhoto(index) {
        if (this.photos[index]) {
            window.open(this.photos[index].url, '_blank');
        }
    }

    /**
     * Удаление фотографии
     */
    async deletePhoto(index) {
        if (!confirm('Удалить эту фотографию?')) {
            return;
        }

        try {
            const personId = getPersonIdFromUrl();
            const response = await fetch(`/api/person/${personId}/photos/${index}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Ошибка удаления фотографии');
            }

            this.photos.splice(index, 1);
            this.renderPhotos();

            if (window.showSuccess) {
                showSuccess('Фотография удалена');
            }

        } catch (error) {
            console.error('Ошибка удаления фотографии:', error);
            if (window.showError) {
                showError('Ошибка удаления фотографии');
            }
        }
    }

    /**
     * Показать пустое состояние
     */
    showEmptyState() {
        const container = document.getElementById('photosGrid');
        if (!container) return;

        let content;
        if (this.sortMode) {
            content = `
                <div class="empty-state">
                    <div class="empty-icon">📷</div>
                    <h3>Нет фотографий для сортировки</h3>
                    <p>Сначала добавьте фотографии, чтобы изменить их порядок</p>
                </div>
            `;
        } else {
            content = `
                <div class="empty-state">
                    <div class="empty-icon">📷</div>
                    <h3>Нет фотографий</h3>
                    <p>Перетащите файлы сюда или нажмите кнопку "Добавить фото"</p>
                </div>
            `;
        }

        container.innerHTML = content;
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
window.PersonPhotos = PersonPhotos;
