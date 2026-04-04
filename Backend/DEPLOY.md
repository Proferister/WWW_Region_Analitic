# Инструкция по запуску

## Требования

- Ubuntu 22.04+
- Python 3.12+
- PostgreSQL 14+
- nginx с HTTPS (Let's Encrypt)
- Доменное имя (whitea.ru)

---

## 1. PostgreSQL

```bash
# Установить если нет
sudo apt install postgresql postgresql-contrib

# Создать БД и пользователя
sudo -u postgres psql -c "CREATE USER hackathon WITH PASSWORD 'ТВОЙ_ПАРОЛЬ';"
sudo -u postgres psql -c "CREATE DATABASE hackathon OWNER hackathon;"
```

---

## 2. AI Migrate (анализ сообщений)

AI Migrate — сервис анализа текста через GigaChat. Работает на порту 8001.

### Установка

```bash
cd /root/hakaton
cp -r "AI Migrate" ai-migrate
cd ai-migrate

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Настройка .env

```bash
cat > .env << 'EOF'
REGION_PULSE_PROVIDER=gigachat
GIGACHAT_MODEL=GigaChat-2-Lite
GIGACHAT_EMBEDDINGS_MODEL=Embeddings-2
GIGACHAT_SCOPE=GIGACHAT_API_PERS
CLIENT_ID=ТВОЙ_CLIENT_ID
CLIENT_SECRET=ТВОЙ_CLIENT_SECRET
GIGACHAT_VERIFY_SSL=false
EOF
```

Получить CLIENT_ID и CLIENT_SECRET:
1. Зарегистрироваться на https://developers.sber.ru
2. Создать проект GigaChat API
3. Получить ключи в разделе "Авторизационные данные"

### systemd сервис

```bash
cat > /etc/systemd/system/ai-migrate.service << 'EOF'
[Unit]
Description=AI Migrate (Region Pulse)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/hakaton/ai-migrate
ExecStart=/root/hakaton/ai-migrate/venv/bin/uvicorn functions.main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=5
EnvironmentFile=/root/hakaton/ai-migrate/.env

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ai-migrate
systemctl start ai-migrate
```

### Проверка

```bash
curl http://127.0.0.1:8001/api/health
# Должно вернуть {"status":"ok",...}
```

---

## 3. Backend (основной сервер)

### Установка

```bash
cd /root/hakaton/backend

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Настройка .env

```bash
cat > .env << 'EOF'
MAX_BOT_TOKEN=ТОКЕН_МАКС_БОТА
WEBHOOK_URL=https://whitea.ru/api/webhook

TG_BOT_TOKEN=ТОКЕН_ТЕЛЕГРАМ_БОТА
TG_WEBHOOK_URL=https://whitea.ru/api/tg-webhook

HOST=0.0.0.0
PORT=8000

DATABASE_URL=postgresql+asyncpg://hackathon:ПАРОЛЬ_БД@localhost:5432/hackathon

AI_MIGRATE_URL=http://127.0.0.1:8001

MAIL_API_URL=https://whitea.ru/api/mail/send
MAIL_API_KEY=КЛЮЧ_MAIL_API

JWT_SECRET=СГЕНЕРИРОВАТЬ_КОМАНДОЙ_НИЖЕ
EOF
```

Сгенерировать JWT_SECRET:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Получение токенов ботов

**MAX бот:**
1. Открыть https://business.max.ru/self
2. Чат-боты → Интеграция → Получить токен

**Telegram бот:**
1. Написать @BotFather в Telegram
2. /newbot → получить токен

### systemd сервис

```bash
cat > /etc/systemd/system/hackathon-backend.service << 'EOF'
[Unit]
Description=Hackathon Backend API
After=network.target postgresql.service ai-migrate.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/hakaton/backend
ExecStart=/root/hakaton/backend/venv/bin/python -m app.main
Restart=always
RestartSec=5
EnvironmentFile=/root/hakaton/backend/.env

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable hackathon-backend
systemctl start hackathon-backend
```

### Проверка

```bash
# Логи
journalctl -u hackathon-backend -f

# Проверить API
curl http://127.0.0.1:8000/docs
```

При первом запуске таблицы БД создадутся автоматически. Если ошибка прав:

```bash
sudo -u postgres psql -d hackathon -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO hackathon;"
sudo -u postgres psql -d hackathon -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO hackathon;"
```

---

## 4. nginx

### Конфигурация

```nginx
server {
    server_name whitea.ru www.whitea.ru;

    root /var/www/whitea;
    index index.html;

    # MAX Webhook (открыт для серверов MAX)
    location = /api/webhook {
        proxy_pass http://127.0.0.1:8000/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Telegram Webhook (открыт для серверов Telegram)
    location = /api/tg-webhook {
        proxy_pass http://127.0.0.1:8000/tg-webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API (авторизация, источники, дашборд)
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Authorization $http_authorization;
    }

    # Фронтенд
    location / {
        try_files $uri $uri.html $uri/ =404;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/whitea.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/whitea.ru/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

server {
    listen 80;
    server_name whitea.ru www.whitea.ru;
    return 301 https://$host$request_uri;
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## 5. Порядок запуска

```bash
# 1. PostgreSQL (обычно уже запущен)
systemctl status postgresql

# 2. AI Migrate (порт 8001)
systemctl start ai-migrate
# Подождать 5 секунд
curl http://127.0.0.1:8001/api/health

# 3. Backend (порт 8000)
systemctl start hackathon-backend
# Подождать 5 секунд
journalctl -u hackathon-backend -n 20

# 4. nginx (уже запущен)
systemctl status nginx
```

---

## 6. Проверка работоспособности

### Авторизация
```bash
curl -s -X POST https://whitea.ru/api/auth/request-otp \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'
```

### Источники (нужен токен)
```bash
curl -s https://whitea.ru/api/sources \
  -H "Authorization: Bearer ТОКЕН"
```

### Дашборд
```bash
curl -s https://whitea.ru/api/dashboard/topics \
  -H "Authorization: Bearer ТОКЕН"
```

### AI Migrate напрямую
```bash
curl -s -X POST http://127.0.0.1:8001/api/analyze-message \
  -H "Content-Type: application/json" \
  -d '{"text":"В Аксайском районе не вывозят мусор","channel_name":"Новости"}'
```

---

## 7. Логи и мониторинг

```bash
# Backend
journalctl -u hackathon-backend -f

# AI Migrate
journalctl -u ai-migrate -f

# nginx
tail -f /var/log/nginx/error.log

# PostgreSQL
sudo -u postgres psql -d hackathon -c "SELECT count(*) FROM messages;"
sudo -u postgres psql -d hackathon -c "SELECT count(*) FROM topics;"
sudo -u postgres psql -d hackathon -c "SELECT count(*) FROM sources WHERE status='approved';"
```

---

## 8. Фоновые процессы

При запуске Backend автоматически стартуют:

| Задача | Интервал | Что делает |
|--------|---------|-----------|
| cleanup_loop | 1 час | Удаляет истёкшие OTP и старые отозванные токены |
| poll_rss_sources | 10 мин | Собирает новые записи из RSS/ATOM фидов |
| analyze_loop | 30 сек | Анализирует новые сообщения через AI Migrate |
| build_topics_loop | 5 мин | Строит топ-10 проблем через кластеризацию |

---

## 9. Полезные команды

```bash
# Перезапуск всего
systemctl restart ai-migrate && sleep 3 && systemctl restart hackathon-backend

# Очистить все данные
sudo -u postgres psql -d hackathon -c "TRUNCATE messages, topics, sources, otp_codes, revoked_tokens, users RESTART IDENTITY CASCADE;"

# Посмотреть размер БД
sudo -u postgres psql -d hackathon -c "SELECT pg_size_pretty(pg_database_size('hackathon'));"

# Проверить статус сервисов
systemctl status hackathon-backend ai-migrate postgresql nginx
```
