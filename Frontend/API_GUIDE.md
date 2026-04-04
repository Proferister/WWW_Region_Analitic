# Задачи для фронтенд-разработчика

## Базовый URL API

```
https://whitea.ru/api
```

---

## 1. Подключить MAX Bridge

В `index.html` добавить:

```html
<script src="https://st.max.ru/js/max-web-app.js"></script>
```

Хелпер определения контекста:

```typescript
function isInsideMax(): boolean {
  return !!window.WebApp?.initData;
}
```

---

## 2. Страница авторизации (LoginPage)

### Что реализовать

**В браузере** — только форма email + OTP:
1. Ввод email → `POST /auth/request-otp` → код приходит на почту
2. Ввод 6-значного кода → `POST /auth/verify-otp` → получаем `token` и `role`
3. Сохранить `token` и `role` в localStorage → перейти на dashboard

**В MAX** (isInsideMax() === true) — то же + кнопка «Гостевой вход»:
- Кнопка «Гостевой вход» → `POST /auth/guest` с `init_data` из `window.WebApp.initData`
- Получаем `token` и `role: "guest"` → перейти на dashboard (только просмотр)

### API

| Метод | Путь | Тело | Ответ 200 |
|-------|------|------|-----------|
| POST | /auth/request-otp | `{ "email": "..." }` | `{ "status": "ok", "message": "Код отправлен на почту" }` |
| POST | /auth/verify-otp | `{ "email": "...", "code": "482917" }` | `{ "status": "ok", "token": "eyJ...", "role": "staff" }` |
| POST | /auth/guest | `{ "init_data": "..." }` | `{ "status": "ok", "token": "eyJ...", "role": "guest" }` |

### Ошибки
- 400 — неверный/просроченный код
- 401 — невалидные данные MAX Bridge (гостевой вход не из MAX)
- 422 — невалидный email

---

## 3. Выход из системы

Кнопка «Выход» → `POST /auth/logout` с заголовком `Authorization: Bearer <token>`:
1. Вызвать API
2. Удалить `token` и `role` из localStorage
3. Перейти на страницу логина

---

## 4. Обработка истёкшего токена

При **любом** запросе к API, если ответ `401`:
1. Удалить `token` и `role` из localStorage
2. Перенаправить на страницу авторизации

Это уже реализовано в `authFetch` (см. готовый код ниже).

---

## 5. Ограничение по ролям

| Роль | Доступ |
|------|--------|
| `staff` | Полный: дашборд, источники, отчёты, управление |
| `guest` | Только просмотр дашборда |

**Что скрыть для гостей:**
- Кнопка «Управление источниками»
- Кнопка «Экспорт отчёта»
- Кнопки подтверждения/отклонения источников
- Любые действия по изменению данных

**Что показать гостям:**
- Баннер «Вы в гостевом режиме. Доступен только просмотр.»

```typescript
{isStaff() && <Button>Управление источниками</Button>}
{isGuest() && <Alert message="Вы в гостевом режиме. Доступен только просмотр." />}
```

---

## 6. Страница источников (SourcesPage)

### Что реализовать

Страница состоит из двух блоков:

#### Блок 1 — Ожидают подтверждения (только staff)

Загружать через `GET /sources/pending`. Для каждого источника показать:
- Название группы
- Описание (если есть)
- Платформа (MAX)
- Две кнопки: **Подключить** и **Отклонить**

| Кнопка | API | Результат |
|--------|-----|-----------|
| Подключить | `POST /sources/{id}/approve` | Источник переходит в список подключённых |
| Отклонить | `POST /sources/{id}/reject` | Источник исчезает, бот покидает группу |

#### Блок 2 — Подключённые источники

Загружать через `GET /sources` и фильтровать `status === "approved"`. Для каждого:
- Название
- Описание
- Платформа (бейдж MAX)
- Статус (зелёный индикатор)
- Кнопка удаления (только staff)

### Как источники появляются

```
1. Сотрудник добавляет бота @ИМЯ_БОТА в группу в мессенджере MAX
2. Бот автоматически сохраняет группу в БД (status: "pending")
3. На странице источников в блоке "Ожидают подтверждения" появляется новая запись
4. Сотрудник нажимает "Подключить" → status: "approved", источник в основном списке
5. Или "Отклонить" → бот покидает группу, запись удаляется из видимых
```

### API источников

| Метод | Путь | Доступ | Описание |
|-------|------|--------|----------|
| GET | /sources | staff, guest | Все источники |
| GET | /sources/pending | staff | Только ожидающие |
| POST | /sources | staff | Добавить вручную |
| PATCH | /sources/{id} | staff | Обновить (is_active, name, description) |
| POST | /sources/{id}/approve | staff | Подтвердить |
| POST | /sources/{id}/reject | staff | Отклонить (бот покидает чат) |
| DELETE | /sources/{id} | staff | Удалить |

### Формат объекта Source

```typescript
interface Source {
  id: number;
  platform: "max";            // пока только MAX
  name: string;               // название группы
  description: string | null; // описание группы
  source_id: string;          // chat_id в MAX
  source_url: string | null;
  status: "pending" | "approved" | "rejected";
  is_active: boolean;
  created_at: string;         // ISO 8601
}
```

### Отображение статусов

```typescript
function statusBadge(status: string) {
  switch (status) {
    case 'approved': return { color: 'green', text: 'Подключён' };
    case 'pending':  return { color: 'orange', text: 'Ожидает' };
    case 'rejected': return { color: 'red', text: 'Отклонён' };
    default:         return { color: 'gray', text: status };
  }
}
```

---

## 7. Обновление токена

Токен живёт 24 часа. Для продления сессии:

```
POST /auth/refresh
Authorization: Bearer <текущий_токен>
→ { "status": "ok", "token": "новый_токен" }
```

---

## Готовый код — `src/api.ts`

Создай файл и скопируй:

```typescript
const API_URL = 'https://whitea.ru/api';

// --- Контекст ---

export function isInsideMax(): boolean {
  return !!window.WebApp?.initData;
}

// --- Авторизация ---

export async function requestOtp(email: string) {
  const res = await fetch(`${API_URL}/auth/request-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) throw await res.json();
  return res.json();
}

export async function verifyOtp(email: string, code: string) {
  const res = await fetch(`${API_URL}/auth/verify-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, code }),
  });
  if (!res.ok) throw await res.json();
  const data = await res.json();
  localStorage.setItem('token', data.token);
  localStorage.setItem('role', data.role);
  return data;
}

export async function guestLogin() {
  const initData = window.WebApp?.initData;
  if (!initData) throw new Error('Гостевой вход доступен только из MAX');
  const res = await fetch(`${API_URL}/auth/guest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ init_data: initData }),
  });
  if (!res.ok) throw await res.json();
  const data = await res.json();
  localStorage.setItem('token', data.token);
  localStorage.setItem('role', data.role);
  return data;
}

export async function logout() {
  const token = localStorage.getItem('token');
  if (token) {
    await fetch(`${API_URL}/auth/logout`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
    }).catch(() => {});
  }
  localStorage.removeItem('token');
  localStorage.removeItem('role');
}

export async function refreshToken() {
  const token = localStorage.getItem('token');
  if (!token) throw new Error('Нет токена');
  const res = await fetch(`${API_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!res.ok) throw await res.json();
  const data = await res.json();
  localStorage.setItem('token', data.token);
  return data;
}

// --- Хелперы ---

export function getRole(): string {
  return localStorage.getItem('role') || '';
}

export function isStaff(): boolean {
  return getRole() === 'staff';
}

export function isGuest(): boolean {
  return getRole() === 'guest';
}

export function isLoggedIn(): boolean {
  return !!localStorage.getItem('token');
}

export async function authFetch(url: string, options: RequestInit = {}) {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_URL}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });
  if (res.status === 401) {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    window.location.reload();
  }
  return res;
}

// --- Источники ---

export async function getSources() {
  const res = await authFetch('/sources');
  if (!res.ok) throw await res.json();
  return res.json();
}

export async function getPendingSources() {
  const res = await authFetch('/sources/pending');
  if (!res.ok) throw await res.json();
  return res.json();
}

export async function createSource(data: {
  platform: 'max';
  name: string;
  description?: string;
  source_id: string;
}) {
  const res = await authFetch('/sources', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await res.json();
  return res.json();
}

export async function updateSource(id: number, data: {
  is_active?: boolean;
  name?: string;
  description?: string;
}) {
  const res = await authFetch(`/sources/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await res.json();
  return res.json();
}

export async function approveSource(id: number) {
  const res = await authFetch(`/sources/${id}/approve`, { method: 'POST' });
  if (!res.ok) throw await res.json();
  return res.json();
}

export async function rejectSource(id: number) {
  const res = await authFetch(`/sources/${id}/reject`, { method: 'POST' });
  if (!res.ok) throw await res.json();
  return res.json();
}

export async function deleteSource(id: number) {
  const res = await authFetch(`/sources/${id}`, { method: 'DELETE' });
  if (!res.ok) throw await res.json();
  return res.json();
}
```

---

## Памятка

| Параметр | Значение |
|----------|----------|
| OTP-код | 6 цифр, действителен 5 минут |
| JWT-токен | действителен 24 часа |
| Письма от | no-reply@whitea.ru |
| При 401 | удалить token + role из localStorage → редирект на логин |
| Гостевой вход | только из MAX, только просмотр |
| После logout | токен отозван на сервере, повторно не работает |
| Источники MAX | добавляются автоматически при добавлении бота в группу |
| Подтверждение | только через приложение (кнопки Подключить/Отклонить) |
