# Region Analytic

ИИ-ассистент объективной аналитики новостей и социальных сетей для органов власти.

Система в реальном времени собирает публичные сообщения о жизни региона, автоматически анализирует их с помощью нейросети GigaChat и формирует топ-10 наиболее острых проблем для принятия управленческих решений.

## Возможности

- **Сбор данных** из мессенджеров MAX и Telegram (через ботов), а также новостных RSS/ATOM лент
- **ИИ-анализ** каждого сообщения: классификация по 13 отраслевым категориям, определение тональности, извлечение геолокации и ключевых слов
- **Топ-10 проблем** региона с нейтральными сводками, динамикой, географией привязки и ссылками на первоисточники
- **Фильтрация шума** — дедупликация (20% схожесть), отсев позитивных/нейтральных сообщений, проверка доверенности источников
- **Детальные карточки** по каждой проблеме: сводка, статистика, график динамики, проверка достоверности, список источников
- **PDF-отчёты** с возможностью скачивания и отправки через бота в мессенджер
- **Авторизация** по email + OTP для сотрудников, гостевой режим через MAX Bridge
- **Управление источниками** — подключение/отключение групп и каналов через веб-интерфейс

## Архитектура

```
Источники данных              Обработка                    Представление

MAX группы ──webhook──┐
TG группы  ──webhook──┼──► Collector ──► Analyzer ──► Topics ──► Dashboard
RSS ленты  ──polling──┘    (сбор)       (GigaChat)   (топ-10)   (веб/MAX)
```

## Стек технологий

### Backend
- **Python 3.12**, **FastAPI**, **Uvicorn**
- **PostgreSQL** + **SQLAlchemy 2.0** (async) + **asyncpg**
- **GigaChat-2** (Сбер) — классификация, тональность, кластеризация, embeddings
- **httpx** — async HTTP-клиент для MAX API, Telegram Bot API, GigaChat
- **PyJWT** — авторизация (JWT HS256)
- **fpdf2** — генерация PDF-отчётов

### Frontend
- **React 19** + **TypeScript** + **Vite**
- **Ant Design** — UI-компоненты
- **@ant-design/charts** — графики динамики

### Инфраструктура
- **nginx** — reverse proxy, SSL
- **Let's Encrypt** — HTTPS-сертификаты
- **systemd** — управление сервисами
- **Ubuntu** — серверная ОС

## Категории анализа

ЖКХ | Дороги и транспорт | Здравоохранение | Образование | Экология и ЧС | Экономика и промышленность | Безопасность и правопорядок | Социальная защита | Культура и спорт | Цифровизация и связь | Сельское хозяйство | Строительство и земля | Религия и духовная жизнь

## Быстрый старт

### 1. Клонирование

```bash
git clone https://github.com/omazda/WWW_Region_Analitic.git
cd WWW_Region_Analitic
```

### 2. Backend

```bash
cd Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. База данных

```bash
sudo bash init_db.sh your_password
```

### 4. Конфигурация

```bash
cp .env.example .env
# Заполнить .env: токены ботов, ключи GigaChat, JWT_SECRET, пароль БД
```

Сгенерировать JWT_SECRET:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Запуск

```bash
python -m app.main
```

### 6. Frontend

```bash
cd Frontend
npm install
npm run dev
```

## API

Swagger-документация доступна по адресу `/api/docs` после запуска.

### Основные эндпоинты

| Группа | Путь | Описание |
|--------|------|----------|
| Авторизация | `POST /auth/request-otp` | Запрос OTP-кода на email |
| | `POST /auth/verify-otp` | Проверка кода, получение JWT |
| | `POST /auth/guest` | Гостевой вход (только MAX) |
| | `POST /auth/logout` | Завершение сессии |
| Источники | `GET /sources` | Список источников |
| | `GET /sources/pending` | Ожидающие подтверждения |
| | `POST /sources/rss` | Добавить RSS-источник |
| | `POST /sources/{id}/approve` | Подтвердить источник |
| | `POST /sources/{id}/reject` | Отклонить источник |
| Дашборд | `GET /dashboard/topics` | Топ-10 проблем |
| | `GET /dashboard/topics/{id}` | Детальная карточка |
| | `GET /dashboard/topics/{id}/pdf` | PDF-отчёт |
| Webhook | `POST /webhook` | MAX Bot webhook |
| | `POST /tg-webhook` | Telegram Bot webhook |

## Фоновые задачи

| Задача | Интервал | Описание |
|--------|---------|----------|
| RSS polling | 10 мин | Сбор новостей из RSS/ATOM фидов |
| Анализ сообщений | 30 сек | GigaChat: категория, тональность, геолокация |
| Построение топиков | 5 мин | Кластеризация, формирование топ-10 |
| Очистка БД | 1 час | Удаление истёкших OTP и отозванных токенов |

## Деплой

Подробная инструкция — в файле [DEPLOY.md](Backend/DEPLOY.md).

## Структура проекта

```
Backend/
├── app/
│   ├── main.py           # FastAPI, webhooks, фоновые задачи
│   ├── config.py         # Конфигурация из .env
│   ├── models.py         # Модели БД (users, sources, messages, topics)
│   ├── database.py       # Async-подключение к PostgreSQL
│   ├── auth.py           # Авторизация (OTP, JWT, роли)
│   ├── sources.py        # CRUD источников
│   ├── dashboard.py      # API дашборда и PDF-отчёты
│   ├── collector.py      # Сбор сообщений (MAX, TG, RSS)
│   ├── analyzer.py       # Анализ и построение топиков
│   ├── ai_analyze.py     # GigaChat: классификация, embeddings, кластеризация
│   ├── max_api.py        # Клиент MAX API
│   ├── telegram_api.py   # Клиент Telegram Bot API
│   ├── max_bridge.py     # Валидация MAX Bridge initData
│   ├── rss_parser.py     # Парсер RSS/ATOM
│   ├── mail_service.py   # Отправка OTP на почту
│   ├── pdf_report.py     # Генерация PDF-отчётов
│   └── fonts/            # Шрифты для PDF (DejaVuSans)
├── init_db.sh            # Скрипт развёртывания БД
├── requirements.txt
├── .env.example
├── DEPLOY.md
└── CHANGELOG.md

Frontend/
├── src/
│   ├── App.tsx
│   ├── api.ts            # API-клиент
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── TopicDetailPage.tsx
│   │   └── SourcesPage.tsx
│   └── components/
├── package.json
└── vite.config.ts
```

## Принципы

- Полностью российская инфраструктура — без зарубежных облачных сервисов
- Только публичные данные — соблюдение законодательства
- Объективность — факты без оценочных суждений
- Прозрачность — по каждой теме доступны источники и обоснование

## Наша команда

<h4>Олег teamlead (fullstack) https://t.me/oligovit_6 </h4>
<h4>Кирилл ml https://t.me/MOJEMI </h4>
<h4>Матвей backend https://t.me/jsbe0w0 </h4>
<h4>Никита design https://t.me/Xeolayy </h4>
<h4>Егор speaker https://t.me/egorik2675 </h4>

## Лицензия

Проект создан в рамках хакатона. Все права защищены.
