# Семейное дерево — генерация и просмотр

Этот проект позволяет генерировать и просматривать интерактивное семейное дерево на основе текстового файла с родословной. В комплекте — инструменты для построения структуры, веб-сервер для просмотра и гибкая настройка исходных данных и параметров запуска.

## 1. Запуск основной генерации дерева (`tree_gen/run.py`)

### Требования
- Python 3.7+
- Graphviz (`dot`) для генерации PNG/SVG
- Все зависимости, указанные в проекте (установите через `pip install -r requirements.txt`, если есть requirements)

### Запуск
Перейдите в корень проекта и выполните:

```bash
python3 tree_gen/run.py
```


## 2. Запуск сервера (`start_server.py`)

### Требования
- Python 3.7+

### Запуск
Из корня проекта выполните:

```bash
python3 start_server.py
```

Скрипт автоматически определит рабочую директорию и запустит сервер из папки `site`.

Основной pipeline сначала обновляет `family_tree.ged`, затем строит
`site/family_tree_vector.svg` уже из GEDCOM-модели. Это держит сайт совместимым
с генеалогическим форматом и сохраняет прежние SVG ID вида `node<ID>`.

## 3. Экспорт и рендер из GEDCOM

Для обмена данными с генеалогическими программами можно экспортировать
`source.txt` в GEDCOM 5.5.1:

```bash
python3 tree_gen/export_gedcom.py source.txt -o family_tree.ged
```

Файл `family_tree.ged` содержит персональные данные и не коммитится в git.

Чтобы построить сайтовый SVG из уже готового GEDCOM-файла:

```bash
python3 tree_gen/run_gedcom.py family_tree.ged
```

Команда перезаписывает `site/family_tree_vector.svg`.

## 4. Запуск через Docker Compose

### Требования
- Docker
- Docker Compose
- Локальные файлы `source.txt` и директория `person_data/`

### Запуск
Из корня проекта выполните:

```bash
docker compose up --build
```

Сайт будет доступен по адресу:

```text
https://drevo.gribovka.ru
```

Compose собирает image из кода проекта, но не копирует личные данные внутрь
image. Данные подключаются volume-ами:

- `./source.txt` -> `/data/source.txt` только для чтения
- `./person_data` -> `/data/person_data`
- `./site/family_tree_vector.svg` -> `/app/site/family_tree_vector.svg` только для чтения

Перед первым запуском убедитесь, что дерево сгенерировано:

```bash
python3 tree_gen/run.py
```

Для остановки:

```bash
docker compose down
```

## 5. Конфигурация портов и адреса

- По умолчанию Python-сервер запускается на `127.0.0.1:8000` для локальной разработки. В Docker наружу публикуются только `80` и `443` через Caddy.
- Для изменения адреса и порта создайте или отредактируйте файл `site/config/site_config.py`:

```python
host = '0.0.0.0'  # или другой нужный адрес
port = 5061       # или другой нужный порт
```

- Если файл отсутствует, используются значения по умолчанию.
- В Docker окружение переопределяется переменными:
  - `FAMILY_TREE_HOST`
  - `FAMILY_TREE_PORT`
  - `FAMILY_TREE_DATA_DIR`
  - `FAMILY_TREE_SOURCE_FILE`
  - `FAMILY_TREE_S3_BUCKET`
  - `FAMILY_TREE_S3_ENDPOINT_URL`
  - `FAMILY_TREE_S3_REGION`
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`

## 6. HTTPS и безопасная связь

Docker Compose поднимает два сервиса:

- `family-tree` — Python backend, доступен только внутри Docker-сети на порту `8000`.
- `caddy` — публичная точка входа на портах `80` и `443`, выпускает TLS-сертификат для `drevo.gribovka.ru` и проксирует запросы в backend.

Фронт использует относительные пути (`/api`, `/person_data/...`), поэтому браузер общается с сайтом и API через один HTTPS origin. Публичный порт `9000` не используется.

Для запуска на сервере:

```bash
docker compose up -d --build
```

## 7. Авторизация через Yandex ID

Создайте приложение Yandex ID типа `Веб-сервисы` и укажите Redirect URI:

```text
https://drevo.gribovka.ru/auth/callback
```

Минимальные права:

- доступ к логину, имени и фамилии, полу;
- доступ к адресу электронной почты опционален.

На сервере создайте `.env` из шаблона `.env.example` и заполните значения:

```bash
cp .env.example .env
```

```env
FAMILY_TREE_AUTH_ENABLED=true
YANDEX_CLIENT_ID=...
YANDEX_CLIENT_SECRET=...
YANDEX_REDIRECT_URI=https://drevo.gribovka.ru/auth/callback
YANDEX_ALLOWED_LOGINS=login1,login2
FAMILY_TREE_SESSION_SECRET=<long-random-secret>
```

`YANDEX_ALLOWED_LOGINS` — список логинов Yandex через запятую. Секреты не
коммитьте: `.env` исключен из git.

Для операций изменения данных используйте отдельные списки ролей:

```env
YANDEX_EDITOR_LOGINS=login1
YANDEX_ADMIN_LOGINS=login2
```

Логины из `YANDEX_ALLOWED_LOGINS`, которых нет в `YANDEX_EDITOR_LOGINS` или
`YANDEX_ADMIN_LOGINS`, могут только читать данные. Загрузка/удаление фото,
сообщения, блог и изменение порядка фото доступны только editor/admin.

После изменения `.env` перезапустите сервис:

```bash
docker compose up -d --build
```

## 8. Приватное S3-хранилище фотографий

Фотографии можно хранить в приватном Yandex Object Storage бакете. Браузер
продолжает обращаться к сайту по URL вида `/person_data/photos/...`, а backend
после проверки авторизации читает или пишет объект в S3.

Для production используется бакет:

```text
s3-gribovka
```

Минимальные переменные окружения:

```env
FAMILY_TREE_S3_BUCKET=s3-gribovka
FAMILY_TREE_S3_ENDPOINT_URL=https://storage.yandexcloud.net
FAMILY_TREE_S3_REGION=ru-central1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

Бакет должен оставаться приватным. CORS не открывает доступ к приватным
объектам и при текущей схеме backend-proxy не нужен для работы сайта. Если CORS
настраивается на будущее, используйте минимальное правило:

```text
Allowed Origins: https://drevo.gribovka.ru
Allowed Methods: GET, HEAD
Allowed Headers: *
Expose Headers: ETag
MaxAgeSeconds: 3600
```

## 9. Операционная безопасность

- `person_data` содержит персональные данные и не попадает в git/image. На
  сервере храните этот каталог на зашифрованном volume или диске с ограниченным
  доступом, делайте резервные копии и проверяйте восстановление. При включенном
  S3 новые фотографии хранятся в приватном бакете, а локальные файлы остаются
  fallback-источником до завершения миграции.
- Публично публикуются только порты `80` и `443`; backend доступен только внутри
  Docker-сети.
- Caddy ограничивает размер HTTP body до `10MB`, backend дополнительно проверяет
  размер JSON/upload-запросов.
- Docker base images закреплены digest-ами. При обновлении образов обновляйте
  digest осознанно и прогоняйте сканирование образов (`trivy`/`grype`) в CI или
  перед деплоем.

## 10. Конфигурация исходных данных (`source.txt`)

Файл `source.txt` содержит список людей и их родственные связи в формате:

```
<ID> - <ФИО> (<даты>)
<ID1> -- <ID2> (<ID3,ID4,...>)
```

- Каждая строка с "-" описывает человека.
- Строки с "--" описывают семейные связи: родители и дети.
- Не изменяйте структуру файла без необходимости.
