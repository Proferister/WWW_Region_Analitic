#!/bin/bash
# Скрипт развёртывания базы данных
# Использование: sudo bash init_db.sh [пароль]

set -e

DB_NAME="hackathon"
DB_USER="hackathon"
DB_PASS="${1:-changeme}"

echo "=== Развёртывание базы данных ==="

# 1. Создать пользователя и БД
echo "[1/4] Создание пользователя и базы данных..."
sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';" 2>/dev/null || echo "Пользователь ${DB_USER} уже существует"
sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};" 2>/dev/null || echo "База данных ${DB_NAME} уже существует"

# 2. Создать таблицы
echo "[2/4] Создание таблиц..."
sudo -u postgres psql -d ${DB_NAME} << 'SQL'

-- Пользователи
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(20) DEFAULT 'guest',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);

-- OTP коды
CREATE TABLE IF NOT EXISTS otp_codes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    code VARCHAR(6) NOT NULL,
    is_used BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL
);

-- Отозванные токены
CREATE TABLE IF NOT EXISTS revoked_tokens (
    id SERIAL PRIMARY KEY,
    jti VARCHAR(64) UNIQUE NOT NULL,
    revoked_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_revoked_tokens_jti ON revoked_tokens(jti);

-- Источники данных
CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    platform VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(1000),
    source_id VARCHAR(255) NOT NULL,
    source_url VARCHAR(500),
    avatar_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'pending',
    is_active BOOLEAN DEFAULT true,
    trust_score INTEGER DEFAULT 50,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Сообщения
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id),
    external_id VARCHAR(255),
    text TEXT NOT NULL,
    text_hash VARCHAR(64),
    is_duplicate BOOLEAN DEFAULT false,
    author_name VARCHAR(255),
    published_at TIMESTAMPTZ,
    collected_at TIMESTAMPTZ DEFAULT now(),
    is_analyzed BOOLEAN DEFAULT false,
    category VARCHAR(100),
    sentiment VARCHAR(20),
    region VARCHAR(255),
    city VARCHAR(255),
    district VARCHAR(255),
    summary VARCHAR(500),
    problem_signature VARCHAR(255),
    keywords TEXT
);
CREATE INDEX IF NOT EXISTS ix_messages_text_hash ON messages(text_hash);

-- Топики (топ проблем)
CREATE TABLE IF NOT EXISTS topics (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    summary TEXT,
    category VARCHAR(100) NOT NULL,
    region VARCHAR(255),
    city VARCHAR(255),
    district VARCHAR(255),
    mentions_count INTEGER DEFAULT 0,
    negative_ratio FLOAT DEFAULT 0.0,
    trend_direction VARCHAR(10) DEFAULT 'flat',
    rank_score FLOAT DEFAULT 0.0,
    problem_signature VARCHAR(255),
    keywords TEXT,
    first_seen_at TIMESTAMPTZ,
    last_seen_at TIMESTAMPTZ,
    peak_date TIMESTAMPTZ,
    peak_mentions INTEGER DEFAULT 0,
    trend_data TEXT,
    source_ids TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

SQL

# 3. Выдать права
echo "[3/4] Выдача прав пользователю ${DB_USER}..."
sudo -u postgres psql -d ${DB_NAME} -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ${DB_USER};"
sudo -u postgres psql -d ${DB_NAME} -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ${DB_USER};"
sudo -u postgres psql -d ${DB_NAME} -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${DB_USER};"
sudo -u postgres psql -d ${DB_NAME} -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${DB_USER};"

# 4. Проверка
echo "[4/4] Проверка..."
TABLES=$(sudo -u postgres psql -d ${DB_NAME} -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")
echo "Создано таблиц: ${TABLES}"

echo ""
echo "=== Готово ==="
echo "DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASS}@localhost:5432/${DB_NAME}"
echo ""
echo "Добавьте эту строку в .env"
