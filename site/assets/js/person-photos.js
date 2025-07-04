// Управление фотографиями персоны (упрощенная версия без модальных окон)
class PersonPhotos {
    constructor() {
        this.photos = [];
        this.init();
    }

    init() {
        this.bindEvents();
        this.setupDragAndDrop();
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
     * Настройка drag & drop
     */
    setupDragAndDrop() {
        const photosGrid = document.getElementById('photosGrid');
        if (!photosGrid) return;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            photosGrid.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            photosGrid.addEventListener(eventName, () => {
                photosGrid.classList.add('drag-over');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            photosGrid.addEventListener(eventName, () => {
                photosGrid.classList.remove('drag-over');
            }, false);
        });

        photosGrid.addEventListener('drop', (e) => {
            const files = Array.from(e.dataTransfer.files);
            const imageFiles = files.filter(file => file.type.startsWith('image/'));

            if (imageFiles.length > 0) {
                this.uploadPhotos(imageFiles);
            }
        }, false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
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
    }

    /**
     * Создание HTML для фотографии
     */
    createPhotoHTML(photo, index) {
        return `
            <div class="photo-item" data-index="${index}">
                <div class="photo-wrapper">
                    <img class="photo-image" src="${photo.url}" alt="${this.escapeHtml(photo.caption || 'Фото')}" 
                         loading="lazy" onclick="window.personPhotos.viewPhoto(${index})">
                    <div class="photo-overlay">
                        <div class="photo-actions">
                            <button class="btn btn-sm photo-view" data-index="${index}" title="Просмотр">👁️</button>
                            <button class="btn btn-sm btn-danger photo-delete" data-index="${index}" title="Удалить">🗑️</button>
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

        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📷</div>
                <h3>Нет фотографий</h3>
                <p>Перетащите файлы сюда или нажмите кнопку "Добавить фото"</p>
            </div>
        `;
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
