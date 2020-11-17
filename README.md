# Сервис лайков

Данный документ содержит описание работы и информацию о развертке микросервиса, предназначенного для хранения информации о лайках, поставленных пользователем и отправляющего информацию о новых лайках в сервис интересов пользователей.

Название: `likes`

Структура сервиса:

| Файл                 | Описание                                                          |
| -------------------- | ----------------------------------------------------------------- |
| `likes.py`           | Код микросервиса                                                  |
| `config.yml`         | Конфигурационный файл со строкой подключения к RabbitMQ и MongoDB |
| `run.sh`             | Файл для запуска сервиса из Docker контейнера                     |
| `requirements.txt`   | Верхнеуровневые зависимости                                       |
| `Dockerfile`         | Описание сборки контейнера сервиса                                |
| `docker-compose.yml` | Изолированная развертка сервиса вместе с (RabbitMQ, MongoDB)      |
| `README.md`          | Описание микросервиса                                             |

## API

### RPC

Новый лайк:

```bat
n.rpc.likes.new_like(like_data)

Args: like_data = [user_id, event_id]
Returns: nothing
Dispatch to the `uis`: [user_id, event_id]
```

Отмена лайка:

```bat
n.rpc.likes.cancel_like(like_data)

Args: like_data = [user_id, event_id]
Returns: nothing
Dispatch to the `uis`: [user_id, event_id]
```

Получить список ид мероприятий, которые понравились пользователю:

```bat
n.rpc.likes.get_likes_by_id(user_id)

Args: user_id
Returns: [event_1_id, ..., event_n_id]
```

Узнать, понравилось ли пользователю данное мероприятие:

```bat
n.rpc.likes.is_event_liked(user_id, event_id)

Args: user_id, event_id
Returns: True is event is liked, False otherwise
```

### HTTP

Новый лайк

```rst
POST http://localhost:8000/new_like HTTP/1.1
Content-Type: application/json

[user_id, event_id]
```

Отмена лайка:

```rst
POST http://localhost:8000/cancel_like HTTP/1.1
Content-Type: application/json

[user_id, event_id]
```

Получить список ид мероприятий, которые понравились пользователю:

```rst
GET http://localhost:8000/get_likes/<id> HTTP/1.1
```

Узнать, понравилось ли пользователю данное мероприятие:

```rst
GET http://localhost:8000/is_liked/<user_id>/<event_id> HTTP/1.1
```

## Развертывание и запуск

### Локальный запуск

Для локального запуска микросервиса требуется запустить контейнер с RabbitMQ и MongoDB.

```bat
docker-compose up -d
```

Затем из папки микросервиса вызвать

```bat
nameko run likes
```

Для проверки `rpc` запустите в командной строке:

```bat
nameko shell
```

После чего откроется интерактивная Python среда. Обратитесь к сервису одной из команд, представленных выше в разделе `rpc`.

### Запуск в контейнере

Чтобы запустить микросервис в контейнере вызовите команду:

```bat
docker-compose up
```

> если вы не хотите просмотривать логи, добавьте флаг `-d` в конце

Микросервис запустится вместе с RabbitMQ и MongoDB в контейнерах.

> Во всех случаях запуска вместе с MongoDB также разворачивается mongo-express - инструмент, с помощью которого можно просматривать и изменять содержимое подключенной базы (подключение в контейнерах сконфигурировано и производится автоматически). Сервис хостится локально на порту 8081.
