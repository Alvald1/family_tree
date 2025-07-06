"""
API обработчики для работы с персонами
"""

import json
from utils.response_utils import send_json_response
from services.person_service import PersonService
from services.photo_service import PhotoService
from services.blog_service import BlogService
from services.message_service import MessageService


class PersonAPI:
    def __init__(self, data_dirs):
        self.person_service = PersonService()
        self.photo_service = PhotoService(data_dirs['photos'])
        self.blog_service = BlogService(data_dirs['blog'])
        self.message_service = MessageService(data_dirs['messages'])

    def handle_get(self, handler, path_parts):
        """Обработка GET запросов"""
        person_id = path_parts[3]

        if len(path_parts) == 4:
            # GET /api/person/{id} - информация о персоне
            person_info = self.person_service.get_person_info(person_id)
            send_json_response(handler, person_info)

        elif len(path_parts) == 5:
            resource = path_parts[4]
            if resource == 'photos':
                # GET /api/person/{id}/photos
                photos = self.photo_service.get_photos(person_id)
                send_json_response(handler, photos)
            elif resource == 'blog':
                # GET /api/person/{id}/blog
                posts = self.blog_service.get_posts(person_id)
                send_json_response(handler, posts)
            elif resource == 'messages':
                # GET /api/person/{id}/messages
                messages = self.message_service.get_messages(person_id)
                send_json_response(handler, messages)
            else:
                handler.send_error(404)
        else:
            handler.send_error(404)

    def handle_post(self, handler, path_parts):
        """Обработка POST запросов"""
        person_id = path_parts[3]
        resource = path_parts[4]

        if resource == 'photos':
            self._upload_photo(handler, person_id)
        elif resource == 'blog':
            self._add_blog_post(handler, person_id)
        elif resource == 'messages':
            self._save_messages(handler, person_id)
        else:
            handler.send_error(404)

    def handle_patch(self, handler, path_parts):
        """Обработка PATCH запросов"""
        person_id = path_parts[3]
        resource = path_parts[4]

        if resource == 'photos' and len(
                path_parts) == 6 and path_parts[5] == 'reorder':
            self._reorder_photos(handler, person_id)
        else:
            handler.send_error(404)

    def handle_put(self, handler, path_parts):
        """Обработка PUT запросов"""
        person_id = path_parts[3]
        resource = path_parts[4]

        if resource == 'messages':
            self._save_messages(handler, person_id)
        else:
            handler.send_error(404)

    def handle_delete(self, handler, path_parts):
        """Обработка DELETE запросов"""
        person_id = path_parts[3]
        resource = path_parts[4]
        item_id = int(path_parts[5])

        if resource == 'photos':
            try:
                self.photo_service.delete_photo(person_id, item_id)
                send_json_response(handler, {'success': True})
            except (IndexError, FileNotFoundError):
                handler.send_error(404, "Фотография не найдена")
        elif resource == 'blog':
            try:
                self.blog_service.delete_post(person_id, item_id)
                send_json_response(handler, {'success': True})
            except IndexError:
                handler.send_error(404, "Запись не найдена")
        else:
            handler.send_error(404)

    def _upload_photo(self, handler, person_id):
        """Загрузка фотографии"""
        try:
            content_type = handler.headers.get('Content-Type', '')
            if not content_type.startswith('multipart/form-data'):
                handler.send_error(400, "Неправильный тип содержимого")
                return

            boundary = content_type.split('boundary=')[1]
            content_length = int(handler.headers.get('Content-Length', 0))
            post_data = handler.rfile.read(content_length)

            new_photo = self.photo_service.upload_photo(
                person_id, post_data, boundary)
            send_json_response(handler, {'success': True, 'photo': new_photo})

        except ValueError as e:
            handler.send_error(400, str(e))
        except Exception as e:
            print(f"Ошибка загрузки фотографии: {e}")
            handler.send_error(500)

    def _add_blog_post(self, handler, person_id):
        """Добавление записи в блог"""
        try:
            content_length = int(handler.headers.get('Content-Length', 0))
            post_data = handler.rfile.read(content_length).decode('utf-8')
            post_info = json.loads(post_data)

            self.blog_service.add_post(person_id, post_info)
            send_json_response(handler, {'success': True})

        except Exception as e:
            print(f"Ошибка добавления записи в блог: {e}")
            handler.send_error(500)

    def _save_messages(self, handler, person_id):
        """Сохранение сообщений"""
        try:
            content_length = int(handler.headers.get('Content-Length', 0))
            post_data = handler.rfile.read(content_length).decode('utf-8')
            messages = json.loads(post_data)

            self.message_service.save_messages(person_id, messages)
            send_json_response(handler, {'success': True})

        except Exception as e:
            print(f"Ошибка сохранения сообщений: {e}")
            handler.send_error(500)

    def _reorder_photos(self, handler, person_id):
        """Изменение порядка фотографий"""
        try:
            content_length = int(handler.headers.get('Content-Length', 0))
            post_data = handler.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)

            new_photos = data.get('photos')
            new_order = data.get('order')

            reordered_photos = self.photo_service.reorder_photos(
                person_id,
                new_photos=new_photos,
                new_order=new_order
            )
            send_json_response(
                handler, {
                    'success': True, 'photos': reordered_photos})

        except ValueError as e:
            handler.send_error(400, str(e))
        except Exception as e:
            print(f"Ошибка изменения порядка фотографий: {e}")
            handler.send_error(500)
