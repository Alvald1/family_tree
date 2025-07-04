# Конфигурация сайта семейного дерева

# Основные настройки
site_name = "Семейное дерево"
site_description = "Интерактивное генеалогическое дерево семьи"
version = "2.0.0"

# Настройки сервера
host = "127.0.0.1"
port = 8000
debug = True

# Пути к файлам
data_directory = "person_data"
photos_directory = "person_data/photos"
messages_directory = "person_data/messages"
blog_directory = "person_data/blog"

# Настройки загрузки файлов
max_file_size = 10 * 1024 * 1024  # 10MB
allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
thumbnail_size = (300, 300)

# Настройки безопасности
enable_cors = True
allowed_origins = ["*"]
max_upload_files = 10

# Настройки кэширования
cache_static_files = True
cache_max_age = 3600  # 1 час

# Настройки резервного копирования
backup_enabled = True
backup_interval = 24 * 3600  # 24 часа
backup_directory = "backups"
max_backups = 30

# Настройки логирования
log_level = "INFO"
log_file = "server.log"
log_max_size = 10 * 1024 * 1024  # 10MB
log_backup_count = 5
