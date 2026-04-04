# Changelog

## [0.10.0] - 2026-04-04

### Added
- Аватарки источников — `avatar_url` в интерфейсе Source, `<Avatar>` с fallback на иконку платформы
- Инструкция подключения Telegram — отдельный collapsible блок с 3 шагами
- `.env` файл — ссылки на ботов вынесены в переменные окружения (`VITE_TELEGRAM_BOT_*`, `VITE_MAX_BOT_*`, `VITE_API_URL`)

### Changed
- `api.ts` — API_URL берётся из `import.meta.env.VITE_API_URL`
- SourcesPage — два раздельных collapsible блока инструкций (MAX + Telegram)
- Бейджи платформ с иконками (CommentOutlined для MAX, SendOutlined для TG)

## [0.9.0] - 2026-04-04

### Changed
- **Dashboard** — кнопки в шапке заменены на toolbar с подписями ("Источники", "Выход")
- Кнопка "Источники" показывает Badge с количеством pending-источников
- **Навигация упрощена**: Login → Dashboard (без промежуточного экрана ConnectSourcesPage)
- **SourcesPage** — добавлен collapsible блок "Как добавить источник" с 3-шаговой инструкцией
- Инструкция раскрыта по умолчанию если нет ни одного источника
- Пустое состояние: подсказка "Добавьте бота в группу MAX"

### Removed
- `ConnectSourcesPage` — удалена, инструкции перенесены в SourcesPage

## [0.8.0] - 2026-04-04

### Changed
- **SourcesPage** полностью переписана: реальные API-вызовы вместо мок-данных
- Два блока: "Ожидают подтверждения" (pending) + "Подключённые" (approved)
- Кнопки "Подключить" / "Отклонить" для pending-источников (только staff)
- Удаление подключённых источников с подтверждением (только staff)
- Загрузка данных из API: `GET /sources`, `GET /sources/pending`
- Loading-спиннер при загрузке
- Убрано модальное окно добавления (источники добавляются автоматически через бота MAX)

### Added
- Функции API источников в `api.ts`: `getSources`, `getPendingSources`, `createSource`, `updateSource`, `approveSource`, `rejectSource`, `deleteSource`

## [0.7.0] - 2026-04-04

### Added
- Гостевой вход через MAX Bridge (`guestLogin`, `isInsideMax`)
- Кнопка "Гостевой вход (только просмотр)" на LoginPage (только в контексте MAX)
- MAX Bridge скрипт в `index.html`
- TypeScript декларация `window.WebApp` (`src/global.d.ts`)
- Функция `logout()` — серверный logout + очистка localStorage
- Кнопка выхода (LogoutOutlined) в шапке Dashboard
- Роли: `staff` / `guest` — сохранение в localStorage
- Хелперы: `isStaff()`, `isGuest()`, `isLoggedIn()`, `getRole()`
- Ролевые ограничения: кнопка "Источники" скрыта для гостей
- Баннер "Вы в гостевом режиме" для гостей на Dashboard

### Changed
- `api.ts` — полностью обновлён: добавлены `guestLogin`, `logout`, роли, `isInsideMax`
- `verifyOtp` теперь сохраняет `role` в localStorage
- `authFetch` при 401 очищает и `token`, и `role`

## [0.6.0] - 2026-04-04

### Added
- API-клиент (`src/api.ts`) — `requestOtp`, `verifyOtp`, `refreshToken`, `authFetch`
- Интеграция авторизации в LoginPage: реальные запросы к `https://whitea.ru/api`
- Loading-состояние кнопок при запросах
- Обработка ошибок API с `message.error()`
- Повторная отправка кода через API
- Проверка токена в localStorage при загрузке — автоматический переход на Dashboard
- При 401 ответе — очистка токена и редирект на логин

## [0.5.0] - 2026-04-04

### Added
- Sources Management page (`SourcesPage`) — управление подключёнными источниками
- Список источников с бейджами платформ (TG / MAX / WEB), статусом (Активен/Неактивен), кнопкой удаления
- Модальное окно добавления источника: выбор платформы (Telegram / Max / Веб), ввод имени/URL
- Удаление источника с подтверждением (Popconfirm)
- Кнопка перехода к источникам из Dashboard (иконка в шапке)
- Кнопка "Назад" для возврата к Dashboard
- Мок-данные: 4 предустановленных источника

## [0.4.0] - 2026-04-04

### Added
- Topic Detail page (`TopicDetailPage`) — экран детальной карточки проблемы
- Блок "Сводка" — стеклянная карточка с текстом сводки
- Блок "Почему в топе?" — 3 stat-карточки (упоминания, география, негатив)
- Блок "Динамика" — line chart через `@ant-design/charts` (дни × упоминания)
- Блок "Проверка достоверности" — цветной индикатор (зелёный/жёлтый/серый) + фильтрация ботов
- Кнопка "Поделиться"
- Блок "Источники" — список источников с бейджами платформ (TG/MAX), каналом, сообщением, датой, ссылкой
- Кнопка "Назад" для возврата к Dashboard
- Бейдж "#N в топ-10"
- Мок-данные для всех блоков
- Навигация Dashboard → TopicDetail по клику на строку таблицы

### Dependencies
- `@ant-design/charts` — библиотека графиков

## [0.3.0] - 2026-04-04

### Added
- Dashboard page (`DashboardPage`) — экран "Топ-10" проблем Ростовской области
- Ant Design `Table` с горизонтальным скроллом и колонками: Ранг, Заголовок, Отрасль, Геолокация, Динамика, Упоминания
- Ant Design `Segmented` для переключения периода (Сегодня / Неделя / Месяц)
- Кнопка "Фильтры" с иконкой
- Цветные `Tag` бейджи отраслей (ЖКХ, Транспорт, Здравоохранение, Образование, Экология, Экономика)
- Индикаторы динамики: стрелка вверх (красная), вниз (зелёная), стабильно (серая)
- Счётчик упоминаний с иконкой
- Мок-данные 10 проблем
- Навигация ConnectSources → Dashboard через `onSuccess`

## [0.2.0] - 2026-04-04

### Added
- Connect Sources page (`ConnectSourcesPage`) — экран подключения источников после авторизации
- Секция "Подключите источники" с кнопками (чат, веб, Telegram) в glassmorphism стиле
- Секция "Выполните 3 этапа" с пошаговыми инструкциями (копирование бота, открытие Telegram, выдача прав)
- Кнопка "Я добавил бота" для подтверждения
- Навигация между страницами Login → ConnectSources через `onSuccess`

## [0.1.0] - 2026-04-04

### Added
- Login page with glassmorphism design (dark/light themes)
- Email input step with "Войти" button
- OTP code verification step: 6-digit input, countdown timer (45 сек), resend functionality
- Theme toggle (dark/light) with persistent state
- WHITEA logo from `public/logo.png` with adaptive sizing and theme-aware color inversion
- Unbounded font for branding title
- Fully responsive layout (mobile / tablet / desktop)
- Ant Design integration with custom glass-styled components
