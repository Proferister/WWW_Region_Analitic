# MAX API Documentation

## Обзор

API (Application Programming Interface) — это посредник между разработчиком приложений и средой. API MAX — это интерфейс, который позволяет ботам взаимодействовать с платформой и получать необходимые данные с помощью HTTPS-запросов к серверу.

**Базовый URL:** `https://platform-api.max.ru`

---

## Методы HTTP

HTTPS-запросы на домен `platform-api.max.ru` вызывают методы — условные команды:

| Метод | Описание |
|-------|----------|
| GET | Получить ресурсы |
| POST | Создать ресурсы (например, отправить новые сообщения) |
| PUT | Редактировать ресурсы |
| DELETE | Удалить ресурсы |
| PATCH | Исправить ресурсы |

Примеры запросов:
- `GET https://platform-api.max.ru/messages/{messageId}`
- `POST https://platform-api.max.ru/messages`
- `PATCH https://platform-api.max.ru/chats/{chatId}`

---

## Аутентификация

**Заголовок:** `Authorization: <token>`

Передача токена через query-параметры больше не поддерживается.

Токен получается на платформе: `business.max.ru/self` -> Чат-боты -> Интеграция -> Получить токен.

> Токен может быть отозван при нарушении правил платформы.

---

## Коды ответов HTTP

| Код | Описание |
|-----|----------|
| 200 | Успешная операция |
| 400 | Недействительный запрос |
| 401 | Ошибка аутентификации |
| 404 | Ресурс не найден |
| 405 | Метод не допускается |
| 429 | Превышено количество запросов |
| 503 | Сервис недоступен |

Пример JSON-ответа:
```json
{
  "user_id": 1,
  "name": "My Bot",
  "username": "my_bot",
  "is_bot": true,
  "last_activity_time": 1737500130100
}
```

---

## Рекомендации по использованию

- **Long Polling** — для разработки и тестирования
- **Webhook** — только для production-окружения
- Максимальное количество запросов: **30 rps**
- Для вебхуков поддерживается только протокол **HTTPS** (включая самоподписанные сертификаты). HTTP не поддерживается.

---

## Клавиатура

Клавиатура позволяет отправлять боту запросы кнопками, а не сообщениями.

Inline-клавиатура позволяет разместить под сообщением бота до **210** кнопок, сгруппированных в **30** рядов — до **7** кнопок в каждом (до **3**, если это кнопки типа `link`, `open_app`, `request_geo_location` или `request_contact`).

Для кнопки с видом `link` максимальный размер ссылки — **2048 символов**.

### Типы кнопок

| Тип | Описание |
|-----|----------|
| `callback` | Сервер MAX отправляет событие с типом `message_callback` (через Webhook или Long polling) |
| `link` | Открывает ссылку в новой вкладке |
| `request_contact` | Запрашивает у пользователя его контакт и номер телефона |
| `request_geo_location` | Запрашивает у пользователя его местоположение |
| `open_app` | Открывает мини-приложение |
| `message` | Отправляет боту текстовое сообщение |

### Пример inline-клавиатуры

```json
{
  "text": "It is message with inline keyboard",
  "attachments": [
    {
      "type": "inline_keyboard",
      "payload": {
        "buttons": [
          [
            {
              "type": "callback",
              "text": "Press me!",
              "payload": "button1 pressed"
            }
          ]
        ]
      }
    }
  ]
}
```

---

## Форматирование текста

Текст сообщения в чат-боте можно улучшить с помощью базового форматирования. Установите свойство `format` в `NewMessageBody`.

### Markdown (`format: "markdown"`)

| Результат | Синтаксис |
|-----------|-----------|
| *курсив* | `*emphasized*` или `_emphasized_` |
| **жирный** | `**strong**` или `__strong__` |
| ~~зачёркнутый~~ | `~~strikethrough~~` |
| подчёркнутый | `++underline++` |
| `моноширинный` | `` `code` `` |
| ссылка | `[Inline URL](https://dev.max.ru/)` |
| @упоминание | `[Имя Фамилия](max://user/user_id)` |

### HTML (`format: "html"`)

| Результат | Тег |
|-----------|-----|
| *курсив* | `<i>` или `<em>` |
| **жирный** | `<b>` или `<strong>` |
| ~~зачёркнутый~~ | `<del>` или `<s>` |
| подчёркнутый | `<ins>` или `<u>` |
| `моноширинный` | `<pre>` или `<code>` |
| ссылка | `<a href="https://dev.max.ru">Docs</a>` |
| @упоминание | `<a href="max://user/user_id">Имя Фамилия</a>` |

> Вместо `User mention` указывайте полное имя пользователя из профиля в MAX, в том числе фамилию. Если фамилия отсутствует — только имя.

---

## Deep Links

Формат: `https://max.ru/<botName>?start=<payload>`

- `payload` — максимум 128 символов
- При переходе бот получает Update с типом `bot_started`

---

# Эндпоинты API

---

## Bots

### GET /me

Возвращает информацию о боте, идентифицированном по access token.

**Параметры запроса:** Нет

**Тело запроса:** Нет

**Ответ:**

| Поле | Тип | Обязательное | Описание |
|------|-----|-------------|----------|
| user_id | integer (int64) | Да | Идентификатор пользователя/бота |
| first_name | string | Да | Отображаемое имя |
| last_name | string (Nullable) | Нет | Фамилия (не возвращается для ботов) |
| username | string (Nullable) | Нет | Никнейм бота или уникальное публичное имя; может быть null |
| is_bot | boolean | Да | true если это бот |
| last_activity_time | integer (int64) | Да | Последняя активность, Unix timestamp (мс) |
| name | string (Nullable) | Нет | **DEPRECATED** — будет удалено |
| description | string (Nullable) | Нет | До 16000 символов |
| avatar_url | string | Нет | URL уменьшенного аватара |
| full_avatar_url | string | Нет | URL полноразмерного аватара |
| commands | BotCommand[] (Nullable) | Нет | До 32 команд бота |

```bash
curl -X GET "https://platform-api.max.ru/me" \
  -H "Authorization: {access_token}"
```

---

## Chats

### GET /chats

Возвращает список групповых чатов, в которых участвовал бот, информацию о каждом чате и маркер для следующей страницы.

**Query-параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|-------------|----------|
| count | integer [1-100] | Нет | Количество чатов. По умолчанию: 50 |
| marker | integer (int64) | Нет | Указатель на следующую страницу данных. Передайте null для первой страницы |

**Ответ:**

| Поле | Тип | Описание |
|------|-----|----------|
| chats | Chat[] | Список запрошенных чатов |
| marker | integer (int64, Nullable) | Указатель на следующую страницу |

```bash
curl -X GET "https://platform-api.max.ru/chats" \
  -H "Authorization: {access_token}"
```

---

### GET /chats/{chatId}

Возвращает информацию о групповом чате по его ID.

**Path-параметры:**

| Имя | Тип | Описание |
|-----|-----|----------|
| chatId | integer (int64) | ID чата |

**Ответ:**

| Поле | Тип | Описание |
|------|-----|----------|
| chat_id | integer (int64) | ID чата |
| type | enum ChatType | `"chat"` для групповых чатов |
| status | enum ChatStatus | `"active"`, `"removed"`, `"left"`, `"closed"` |
| title | string (Nullable) | Отображаемое название; null для диалогов |
| icon | Image (Nullable) | Иконка чата |
| last_event_time | integer (int64) | Время последнего события |
| participants_count | integer (int32) | Количество участников (всегда 2 для диалогов) |
| owner_id | integer (int64, Nullable) | ID владельца чата |
| participants | object (Nullable) | Участники с временем последней активности |
| is_public | boolean | Публичная доступность (всегда false для диалогов) |
| link | string (Nullable) | Ссылка на чат |
| description | string (Nullable) | Описание чата |
| dialog_with_user | UserWithPhoto (Nullable) | Данные пользователя для типа `"dialog"` |
| chat_message_id | string (Nullable) | ID сообщения с инициирующей кнопкой |
| pinned_message | Message (Nullable) | Закреплённое сообщение (только для запросов конкретного чата) |

```bash
curl -X GET "https://platform-api.max.ru/chats/{chatId}" \
  -H "Authorization: {access_token}"
```

---

### PATCH /chats/{chatId}

Позволяет редактировать информацию о групповом чате: название, иконку, закреплённое сообщение.

**Path-параметры:**

| Имя | Тип | Описание |
|-----|-----|----------|
| chatId | integer (int64) | ID чата |

**Тело запроса:**

| Поле | Тип | Обязательное | Описание |
|------|-----|-------------|----------|
| icon | PhotoAttachmentRequestPayload | Нет | Запрос на прикрепление изображения (поля взаимоисключающие) |
| title | string | Нет | 1-200 символов |
| pin | string | Нет | ID сообщения для закрепления в чате |
| notify | boolean | Нет | По умолчанию: true. Отправляет системное уведомление |

**Ответ:** Объект Chat (аналогично GET /chats/{chatId})

```bash
curl -X PATCH "https://platform-api.max.ru/chats/{chatId}" \
  -H "Authorization: {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"icon": {"url": "https://example.com/image.jpg"}, "title": "Chat Name", "notify": true}'
```

---

### DELETE /chats/{chatId}

Удаляет групповой чат для всех участников.

**Path-параметры:**

| Имя | Тип | Описание |
|-----|-----|----------|
| chatId | integer (int64) | ID чата |

**Ответ:**

| Поле | Тип | Описание |
|------|-----|----------|
| success | boolean | true при успехе |
| message | string | Пояснение при неудаче |

```bash
curl -X DELETE "https://platform-api.max.ru/chats/{chatId}" \
  -H "Authorization: {access_token}"
```

---

### POST /chats/{chatId}/actions

Отправка действия бота в групповой чат (набор текста, отправка фото и т.д.).

**Path-параметры:**

| Имя | Тип | Описание |
|-----|-----|----------|
| chatId | integer (int64) | ID чата |

**Тело запроса:**

| Поле | Тип | Обязательное | Описание |
|------|-----|-------------|----------|
| action | enum SenderAction | Да | Действие бота |

**Значения SenderAction:**

| Значение | Описание |
|----------|----------|
| `typing_on` | Бот набирает сообщение |
| `sending_photo` | Бот отправляет фото |
| `sending_video` | Бот отправляет видео |
| `sending_audio` | Бот отправляет аудио |
| `sending_file` | Бот отправляет файл |
| `mark_seen` | Бот помечает сообщения как прочитанные |

**Ответ:** `{ success: boolean, message?: string }`

```bash
curl -X POST "https://platform-api.max.ru/chats/{chatId}/actions" \
  -H "Authorization: {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"action": "typing_on"}'
```

---

### GET /chats/{chatId}/pin

Возвращает закреплённое сообщение в групповом чате.

**Ответ:**

| Поле | Тип | Описание |
|------|-----|----------|
| message | Message (Nullable) | Закреплённое сообщение. Может быть null |

```bash
curl -X GET "https://platform-api.max.ru/chats/{chatId}/pin" \
  -H "Authorization: {access_token}"
```

---

### PUT /chats/{chatId}/pin

Закрепляет сообщение в групповом чате.

**Тело запроса:**

| Поле | Тип | Обязательное | Описание |
|------|-----|-------------|----------|
| message_id | string | Да | ID сообщения для закрепления (соответствует `Message.body.mid`) |
| notify | boolean (Nullable) | Нет | По умолчанию: true. Участники получают системное уведомление |

**Ответ:** `{ success: boolean, message?: string }`

```bash
curl -X PUT "https://platform-api.max.ru/chats/{chatId}/pin" \
  -H "Authorization: {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"message_id": "{message_id}", "notify": true}'
```

---

### DELETE /chats/{chatId}/pin

Удаляет закреплённое сообщение из группового чата.

**Ответ:** `{ success: boolean, message?: string }`

```bash
curl -X DELETE "https://platform-api.max.ru/chats/{chatId}/pin" \
  -H "Authorization: {access_token}"
```

---

### GET /chats/{chatId}/members/me

Возвращает информацию о членстве текущего бота в групповом чате.

**Ответ:**

| Поле | Тип | Описание |
|------|-----|----------|
| user_id | integer | Идентификатор пользователя/бота |
| first_name | string | Имя |
| last_name | string (Nullable) | Фамилия |
| username | string (Nullable) | Никнейм |
| is_bot | boolean | Является ли ботом |
| last_activity_time | integer | Время последней активности (Unix ms) |
| description | string (Nullable) | До 16000 символов |
| avatar_url | string | URL уменьшенного аватара |
| full_avatar_url | string | URL полноразмерного аватара |
| last_access_time | integer | Время последней активности в чате |
| is_owner | boolean | Является ли владельцем чата |
| is_admin | boolean | Является ли администратором |
| join_time | integer | Unix timestamp присоединения |
| permissions | string[] | Массив прав (см. ниже) |
| alias | string | Отображаемый заголовок |

**Значения permissions:**
`read_all_messages`, `add_remove_members`, `add_admins`, `change_chat_info`, `pin_message`, `write`, `can_call`, `edit_link`, `post_edit_delete_message`, `edit_message`, `delete_message`

```bash
curl -X GET "https://platform-api.max.ru/chats/{chatId}/members/me" \
  -H "Authorization: {access_token}"
```

---

### DELETE /chats/{chatId}/members/me

Удаляет бота из участников группового чата.

**Ответ:** `{ success: boolean, message?: string }`

```bash
curl -X DELETE "https://platform-api.max.ru/chats/{chatId}/members/me" \
  -H "Authorization: {access_token}"
```

---

### GET /chats/{chatId}/members/admins

Возвращает список всех администраторов группового чата. Бот должен быть администратором.

**Ответ:**

| Поле | Тип | Описание |
|------|-----|----------|
| members | ChatMember[] | Список администраторов |
| marker | integer (int64, Nullable) | Указатель на следующую страницу |

```bash
curl -X GET "https://platform-api.max.ru/chats/{chatId}/members/admins" \
  -H "Authorization: {access_token}"
```

---

### POST /chats/{chatId}/members/admins

Назначает администраторов группового чата. Возвращает true при успехе.

**Тело запроса:**

| Поле | Тип | Обязательное | Описание |
|------|-----|-------------|----------|
| admins | ChatAdmin[] | Да | Список пользователей, которые получат права администратора |

**Объект ChatAdmin:**

| Поле | Тип | Описание |
|------|-----|----------|
| user_id | string/integer | ID пользователя |
| permissions | string[] | Массив прав |
| alias | string | Отображаемый заголовок |

**Ответ:** `{ success: boolean, message?: string }`

```bash
curl -X POST "https://platform-api.max.ru/chats/{chatId}/members/admins" \
  -H "Authorization: {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"admins":[{"user_id":"{user_id}","permissions":["read_all_messages","add_remove_members","add_admins","change_chat_info","pin_message","write"],"alias":"Admin"}]}'
```

---

### DELETE /chats/{chatId}/members/admins/{userId}

Отменяет права администратора у пользователя в групповом чате.

**Path-параметры:**

| Имя | Тип | Описание |
|-----|-----|----------|
| chatId | integer (int64) | ID чата |
| userId | integer (int64) | ID пользователя |

**Ответ:** `{ success: boolean, message?: string }`

```bash
curl -X DELETE "https://platform-api.max.ru/chats/{chatId}/members/admins/{userId}" \
  -H "Authorization: {access_token}"
```

---

### GET /chats/{chatId}/members

Возвращает список участников группового чата.

**Query-параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|-------------|----------|
| user_ids | integer[] | Нет | Список ID пользователей; перезаписывает count и marker |
| marker | integer (int64) | Нет | Указатель на следующую страницу |
| count | integer [1-100] | Нет | Количество участников. По умолчанию: 20 |

**Ответ:**

| Поле | Тип | Описание |
|------|-----|----------|
| members | ChatMember[] | Список участников |
| marker | integer (int64, Nullable) | Указатель на следующую страницу |

```bash
curl -X GET "https://platform-api.max.ru/chats/{chatId}/members" \
  -H "Authorization: {access_token}"
```

---

### POST /chats/{chatId}/members

Добавляет участников в групповой чат. Могут потребоваться дополнительные разрешения.

**Тело запроса:**

| Поле | Тип | Обязательное | Описание |
|------|-----|-------------|----------|
| user_ids | integer[] | Да | Массив ID пользователей для добавления |

**Ответ:**

| Поле | Тип | Описание |
|------|-----|----------|
| success | boolean | true при успехе |
| message | string | Пояснение при неудаче |
| failed_user_ids | integer[] | ID пользователей, которых не удалось добавить |
| failed_user_details | object[] | Детальные причины неудач |

```bash
curl -X POST "https://platform-api.max.ru/chats/{chatId}/members" \
  -H "Authorization: {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"user_ids": ["{user_id_1}", "{user_id_2}"]}'
```

---

### DELETE /chats/{chatId}/members

Удаляет участника из группового чата.

**Query-параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|-------------|----------|
| user_id | integer (int64) | Да | ID пользователя для удаления |
| block | boolean | Нет | Если true — пользователь будет заблокирован в чате. Работает только для чатов с публичными/приватными ссылками |

**Ответ:** `{ success: boolean, message?: string }`

```bash
curl -X DELETE "https://platform-api.max.ru/chats/{chatId}/members?user_id={user_id}&block=true" \
  -H "Authorization: {access_token}"
```

---

## Subscriptions

### GET /subscriptions

Если ваш бот получает данные через Webhook, этот метод возвращает список всех подписок.

**Ответ:**

| Поле | Тип | Описание |
|------|-----|----------|
| subscriptions | Subscription[] | Список текущих подписок |

```bash
curl -X GET "https://platform-api.max.ru/subscriptions" \
  -H "Authorization: {access_token}"
```

---

### POST /subscriptions

Настраивает доставку событий бота через Webhook.

**Тело запроса:**

| Поле | Тип | Обязательное | Описание |
|------|-----|-------------|----------|
| url | string | Да | HTTPS URL вашего бота. Должен начинаться с `https://` |
| update_types | string[] | Нет | Список типов обновлений (например, `["message_created", "bot_started"]`) |
| secret | string | Нет | Секрет, отправляемый в заголовке `X-Max-Bot-Api-Secret`. 5-256 символов: A-Z, a-z, 0-9, дефис |

**Ответ:** `{ success: boolean, message?: string }`

**Требования к Webhook:**
- Только HTTPS, порт 443
- Требуется валидация TLS
- Необходимо ответить HTTP 200 в течение 30 секунд
- Политика повторов: до 10 попыток с экспоненциальным откатом (60s, 150s, 375s...)
- Автоматическая отписка если нет успеха в течение 8 часов

---

### DELETE /subscriptions

Отписывает бота от получения обновлений через Webhook. После вызова этого метода становится доступна доставка через long-polling.

**Query-параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|-------------|----------|
| url | string | Да | URL для удаления из подписок Webhook |

**Ответ:** `{ success: boolean, message?: string }`

```bash
curl -X DELETE "https://platform-api.max.ru/subscriptions?url=https://your-domain.com/webhook" \
  -H "Authorization: {access_token}"
```

---

### GET /updates

Получение обновлений. Используется для получения обновлений при разработке и тестировании, когда бот не подписан на Webhook. Использует методологию long polling. Каждое обновление имеет порядковый номер; свойство `marker` указывает на следующее ожидаемое обновление.

**Query-параметры:**

| Имя | Тип | Диапазон | По умолчанию | Обязательный | Описание |
|-----|-----|----------|-------------|-------------|----------|
| limit | integer | [1-1000] | 100 | Нет | Максимальное количество обновлений |
| timeout | integer | [0-90] | 30 | Нет | Таймаут в секундах для long polling |
| marker | int64 | — | — | Нет | Фильтрует необработанные обновления |
| types | string[] | — | — | Нет | Список типов обновлений (например, `message_created`, `message_callback`) |

**Ответ:**

| Поле | Тип | Описание |
|------|-----|----------|
| updates | Update[] | Страница обновлений |
| marker | int64 (Nullable) | Указатель на следующую страницу данных |

```bash
curl -X GET "https://platform-api.max.ru/updates" \
  -H "Authorization: {access_token}"
```

---

## Upload

### POST /uploads

Возвращает URL для последующей загрузки файла.

**Query-параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|-------------|----------|
| type | enum UploadType | Да | Тип загружаемого файла |

**Значения UploadType и поддерживаемые форматы:**

| Тип | Форматы |
|-----|---------|
| `image` | JPG, JPEG, PNG, GIF, TIFF, BMP, HEIC |
| `video` | MP4, MOV, MKV, WEBM, MATROSKA |
| `audio` | MP3, WAV, M4A и другие |
| `file` | Любые типы файлов |

> `photo` — **DEPRECATED**, используйте `type=image`.

**Ответ:**

| Поле | Тип | Описание |
|------|-----|----------|
| url | string | URL для загрузки файла (неограниченный срок жизни) |
| token | string | Токен видео/аудио для отправки в сообщении (опционально) |

**Методы загрузки:**
- **Multipart upload:** Проще, но менее надёжен. `Content-Type: multipart/form-data`. Нельзя возобновить при прерывании.
- **Resumable upload:** Более надёжен, когда `Content-Type` отличается от multipart/form-data. Поддерживает частичную загрузку и возобновление.

**Ограничения:**
- Максимальный размер файла: **4 ГБ**
- Один файл за запрос
- Максимум 30 запросов/секунду

> Ошибка `attachment.not.ready` / `errors.process.attachment.file.not.processed` — добавьте задержку после загрузки; реализуйте логику повторов с увеличивающимися интервалами.

---

## Messages

### GET /messages

Возвращает информацию о сообщении или массив сообщений из чата. Требуется указание `chat_id` или `message_ids`.

**Query-параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|-------------|----------|
| chat_id | integer (int64) | Нет* | ID чата. Обязателен если не указан `message_ids` |
| message_ids | string | Нет* | Список ID сообщений через запятую. Обязателен если не указан `chat_id` |
| from | integer (int64) | Нет | Unix timestamp начала периода |
| to | integer (int64) | Нет | Unix timestamp конца периода |
| count | integer [1-100] | Нет | Максимум сообщений. По умолчанию: 50 |

**Ответ:**

| Поле | Тип | Описание |
|------|-----|----------|
| messages | Message[] | Массив сообщений |

> Сообщения возвращаются в обратном порядке при использовании `chat_id` (сначала новые).

```bash
# По chat_id:
curl -X GET "https://platform-api.max.ru/messages?chat_id={chat_id}" \
  -H "Authorization: {access_token}"

# По message_ids:
curl -X GET "https://platform-api.max.ru/messages?message_ids={id1},{id2}" \
  -H "Authorization: {access_token}"
```

---

### POST /messages

Отправляет сообщение в чат.

**Query-параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|-------------|----------|
| user_id | integer (int64) | Нет | Для отправки конкретному пользователю |
| chat_id | integer (int64) | Нет | Для отправки в групповой чат |
| disable_link_preview | boolean | Нет | Запрещает серверу генерировать превью ссылок |

**Тело запроса (NewMessageBody):**

| Поле | Тип | Ограничения | Обязательное | Описание |
|------|-----|------------|-------------|----------|
| text | string (Nullable) | Макс. 4000 символов | Нет | Текст сообщения |
| attachments | AttachmentRequest[] (Nullable) | — | Нет | Вложения; пустой массив удалит все |
| link | NewMessageLink (Nullable) | — | Нет | Ответ на сообщение |
| notify | boolean | По умолчанию: true | Нет | Управление уведомлениями |
| format | enum | `markdown` или `html` | Нет | Режим форматирования текста |

**Ответ:**

| Поле | Тип | Описание |
|------|-----|----------|
| message | Message | Отправленное сообщение |

---

### PUT /messages

Редактирует сообщение в чате.

**Query-параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|-------------|----------|
| message_id | string (мин. 1 символ) | Да | ID сообщения для редактирования |

**Тело запроса (NewMessageBody):**

| Поле | Тип | Ограничения | Обязательное | Описание |
|------|-----|------------|-------------|----------|
| text | string (Nullable) | Макс. 4000 символов | Нет | Новый текст сообщения |
| attachments | AttachmentRequest[] (Nullable) | — | Нет | Пустой массив удалит все вложения |
| link | NewMessageLink (Nullable) | — | Нет | Ссылка на сообщение |
| notify | boolean | По умолчанию: true | Нет | Управление уведомлениями |
| format | enum (Nullable) | `markdown` или `html` | Нет | Метод форматирования |

**Ответ:** `{ success: boolean, message?: string }`

> Сообщения необходимо редактировать в течение 24 часов после отправки.

---

### DELETE /messages

Удаляет сообщение в диалоге или чате, если бот имеет разрешение на удаление сообщений.

**Query-параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|-------------|----------|
| message_id | string (мин. 1 символ) | Да | ID сообщения для удаления |

**Ответ:** `{ success: boolean, message?: string }`

> Сообщения можно удалять только если они отправлены менее 24 часов назад.

```bash
curl -X DELETE "https://platform-api.max.ru/messages?message_id={message_id}" \
  -H "Authorization: {access_token}"
```

---

### GET /messages/{messageId}

Возвращает сообщение по его ID.

**Path-параметры:**

| Имя | Тип | Паттерн | Описание |
|-----|-----|---------|----------|
| messageId | string | `[a-zA-Z0-9_\-]+` | ID сообщения (`mid`) |

**Ответ:**

| Поле | Тип | Описание |
|------|-----|----------|
| sender | User | Отправитель сообщения |
| recipient | Recipient | Получатель (пользователь или чат) |
| timestamp | integer (int64) | Время создания в Unix-time |
| link | LinkedMessage (Nullable) | Пересланное или ответное сообщение |
| body | MessageBody | Содержание сообщения (текст + вложения). Может быть null |
| stat | MessageStat (Nullable) | Статистика сообщения. Только для постов каналов |
| url | string (Nullable) | Публичная ссылка на пост канала. Отсутствует для диалогов и групповых чатов |

```bash
curl -X GET "https://platform-api.max.ru/messages/{messageId}" \
  -H "Authorization: {access_token}"
```

---

### GET /videos/{videoToken}

Возвращает детальную информацию о прикреплённом видео, включая URL воспроизведения и метаданные.

**Path-параметры:**

| Имя | Тип | Паттерн | Описание |
|-----|-----|---------|----------|
| videoToken | string | `[a-zA-Z0-9_\-]+` | Токен видео-вложения |

**Ответ:**

| Поле | Тип | Описание |
|------|-----|----------|
| token | string | Токен видео-вложения |
| urls | VideoUrls (Nullable) | URL для скачивания/воспроизведения; null если недоступно |
| thumbnail | PhotoAttachmentPayload (Nullable) | Превью видео |
| width | integer | Ширина видео |
| height | integer | Высота видео |
| duration | integer | Длительность видео в секундах |

```bash
curl -X GET "https://platform-api.max.ru/videos/{video_token}" \
  -H "Authorization: {access_token}"
```

---

### POST /answers

Отправляет ответ после нажатия пользователем кнопки. Ответ может быть обновлённым сообщением и/или одноразовым уведомлением для пользователя.

**Query-параметры:**

| Имя | Тип | Обязательный | Описание |
|-----|-----|-------------|----------|
| callback_id | string (мин. 1 символ, паттерн: `^(?!\s*$).+`) | Да | Идентификатор кнопки. Бот получает его как часть Update с типом `message_callback` |

**Тело запроса:**

| Поле | Тип | Обязательное | Описание |
|------|-----|-------------|----------|
| message | NewMessageBody (Nullable) | Нет | Заполните, если хотите изменить текущее сообщение |
| notification | string (Nullable) | Нет | Заполните, если хотите отправить одноразовое уведомление пользователю |

**Ответ:** `{ success: boolean, message?: string }`

```bash
curl -X POST "https://platform-api.max.ru/answers?callback_id=callback_id" \
  -H "Authorization: {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"message": {"text": "Message with button link", "attachments": [{"type": "inline_keyboard", "payload": {"buttons": [[{"type": "link", "text": "Open site", "url": "https://example.com"}]]}}]}}'
```

---

# Объекты данных

## User

| Поле | Тип | Обязательное | Описание |
|------|-----|-------------|----------|
| user_id | integer (int64) | Да | Идентификатор пользователя/бота |
| first_name | string | Да | Отображаемое имя |
| last_name | string (Nullable) | Нет | Фамилия. Не возвращается для ботов |
| username | string (Nullable) | Нет | Никнейм бота или уникальное публичное имя. Может быть null |
| is_bot | boolean | Да | true если это бот |
| last_activity_time | integer (int64) | Нет | Последняя активность в MAX (Unix-time мс). Может отсутствовать если пользователь отключил отображение онлайн |
| name | string (Nullable) | Нет | **DEPRECATED** — будет удалено |

## UserWithPhoto (extends User)

| Поле | Тип | Обязательное | Описание |
|------|-----|-------------|----------|
| description | string (Nullable) | Нет | До 16000 символов. Описание пользователя/бота |
| avatar_url | string | Нет | URL уменьшенного аватара |
| full_avatar_url | string | Нет | URL полноразмерного аватара |

## BotInfo (extends UserWithPhoto)

Возвращается только из `GET /me`.

| Поле | Тип | Обязательное | Описание |
|------|-----|-------------|----------|
| commands | BotCommand[] (Nullable) | Нет | Команды бота, до 32 элементов |

## ChatMember (extends UserWithPhoto)

Возвращается из методов `/chats/{chatId}/members`.

| Поле | Тип | Обязательное | Описание |
|------|-----|-------------|----------|
| last_access_time | integer (int64) | Да | Последняя активность в чате (Unix-time). Может быть устаревшим для суперчатов |
| is_owner | boolean | Да | Является ли пользователь владельцем чата |
| is_admin | boolean | Да | Является ли пользователь администратором |
| join_time | integer (int64) | Да | Дата присоединения (Unix-time) |
| permissions | ChatAdminPermission[] (Nullable) | Нет | Список прав пользователя |
| alias | string | Нет | Заголовок, отображаемый на клиенте |

### Значения ChatAdminPermission

| Значение | Описание |
|----------|----------|
| `read_all_messages` | Чтение всех сообщений |
| `add_remove_members` | Добавление/удаление участников |
| `add_admins` | Добавление администраторов |
| `change_chat_info` | Изменение информации о чате |
| `pin_message` | Закрепление сообщений |
| `write` | Запись сообщений |
| `can_call` | Совершение звонков |
| `edit_link` | Редактирование ссылки |
| `post_edit_delete_message` | Публикация/редактирование/удаление сообщений |
| `edit_message` | Редактирование сообщений |
| `delete_message` | Удаление сообщений |

## Chat

| Поле | Тип | Обязательное | Описание |
|------|-----|-------------|----------|
| chat_id | integer (int64) | Да | ID чата |
| type | enum ChatType | Да | `"chat"` для групповых чатов |
| status | enum ChatStatus | Да | Статус чата |
| title | string (Nullable) | Нет | Отображаемое название. Null для диалогов |
| icon | Image (Nullable) | Нет | Иконка чата |
| last_event_time | integer (int64) | Да | Время последнего события |
| participants_count | integer (int32) | Да | Количество участников (всегда 2 для диалогов) |
| owner_id | integer (int64, Nullable) | Нет | ID владельца чата |
| participants | object (Nullable) | Нет | Участники с временем последней активности. Null при запросе списков чатов |
| is_public | boolean | Да | Публичная доступность (всегда false для диалогов) |
| link | string (Nullable) | Нет | Ссылка/URL чата |
| description | string (Nullable) | Нет | Описание чата |
| dialog_with_user | UserWithPhoto (Nullable) | Нет | Данные пользователя, только для типа `"dialog"` |
| chat_message_id | string (Nullable) | Нет | ID сообщения с кнопкой, инициировавшей чат |
| pinned_message | Message (Nullable) | Нет | Закреплённое сообщение (только для запросов конкретного чата) |

### Значения ChatStatus

| Значение | Описание |
|----------|----------|
| `active` | Бот — активный участник |
| `removed` | Бот удалён из чата |
| `left` | Бот покинул чат |
| `closed` | Чат закрыт |

## Message

| Поле | Тип | Обязательное | Описание |
|------|-----|-------------|----------|
| sender | User | Нет | Отправитель сообщения |
| recipient | Recipient | Да | Получатель (пользователь или чат) |
| timestamp | integer (int64) | Да | Время создания (Unix-time) |
| link | LinkedMessage (Nullable) | Нет | Пересланное или ответное сообщение |
| body | MessageBody | Да | Содержание сообщения (текст + вложения). Может быть null |
| stat | MessageStat (Nullable) | Нет | Статистика. Только для постов каналов |
| url | string (Nullable) | Нет | Публичная ссылка на пост канала. Отсутствует для диалогов/групповых чатов |

## NewMessageBody

Используется для отправки (`POST /messages`) и редактирования (`PUT /messages`) сообщений.

| Поле | Тип | Ограничения | Обязательное | Описание |
|------|-----|------------|-------------|----------|
| text | string (Nullable) | Макс. 4000 символов | Нет | Текст сообщения |
| attachments | AttachmentRequest[] (Nullable) | — | Нет | Вложения. Пустой массив удаляет все |
| link | NewMessageLink (Nullable) | — | Нет | Ссылка на сообщение (ответ/пересылка) |
| notify | boolean | По умолчанию: true | Нет | Если false — участники не получают уведомления |
| format | enum TextFormat (Nullable) | `"markdown"` или `"html"` | Нет | Метод форматирования текста |

## Update

| Поле | Тип | Обязательное | Описание |
|------|-----|-------------|----------|
| update_type | string | Да (по умолчанию: `message_created`) | Тип события |
| timestamp | integer (int64) | Да | Unix-time события |
| message | Message | Да | Новое созданное сообщение (для message_created) |
| user_locale | string (Nullable) | Нет | Язык пользователя (IETF BCP 47). Только в прямых диалогах |

### Значения update_type

| Значение | Описание |
|----------|----------|
| `message_created` | Создано новое сообщение |
| `message_callback` | Нажата callback-кнопка |
| `message_edited` | Сообщение отредактировано |
| `message_removed` | Сообщение удалено |
| `bot_added` | Бот добавлен в чат |
| `bot_removed` | Бот удалён из чата |
| `dialog_muted` | Диалог заглушён |
| `dialog_unmuted` | Диалог разглушён |
| `dialog_cleared` | Диалог очищен |
| `dialog_removed` | Диалог удалён |
| `user_added` | Пользователь добавлен в чат |
| `user_removed` | Пользователь удалён из чата |
| `bot_started` | Пользователь нажал "Начать" |
| `bot_stopped` | Пользователь остановил бота |
| `chat_title_changed` | Изменено название чата |

> Для получения событий из групповых чатов или каналов бот должен быть назначен администратором.

---

# Сводная таблица эндпоинтов

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/me` | Информация о боте |
| GET | `/chats` | Список групповых чатов |
| GET | `/chats/{chatId}` | Информация о чате |
| PATCH | `/chats/{chatId}` | Обновление чата |
| DELETE | `/chats/{chatId}` | Удаление чата |
| POST | `/chats/{chatId}/actions` | Действие бота |
| GET | `/chats/{chatId}/pin` | Получение закреплённого сообщения |
| PUT | `/chats/{chatId}/pin` | Закрепление сообщения |
| DELETE | `/chats/{chatId}/pin` | Удаление закреплённого сообщения |
| GET | `/chats/{chatId}/members/me` | Членство бота |
| DELETE | `/chats/{chatId}/members/me` | Удаление бота из чата |
| GET | `/chats/{chatId}/members/admins` | Список администраторов |
| POST | `/chats/{chatId}/members/admins` | Назначение администратора |
| DELETE | `/chats/{chatId}/members/admins/{userId}` | Отмена прав администратора |
| GET | `/chats/{chatId}/members` | Список участников |
| POST | `/chats/{chatId}/members` | Добавление участников |
| DELETE | `/chats/{chatId}/members` | Удаление участника |
| GET | `/subscriptions` | Получение подписок |
| POST | `/subscriptions` | Подписка на обновления |
| DELETE | `/subscriptions` | Отписка от обновлений |
| GET | `/updates` | Получение обновлений (Long Polling) |
| POST | `/uploads` | Загрузка файлов |
| GET | `/messages` | Получение сообщений |
| POST | `/messages` | Отправка сообщения |
| PUT | `/messages` | Редактирование сообщения |
| DELETE | `/messages` | Удаление сообщения |
| GET | `/messages/{messageId}` | Получение сообщения по ID |
| GET | `/videos/{videoToken}` | Информация о видео |
| POST | `/answers` | Ответ на callback |
