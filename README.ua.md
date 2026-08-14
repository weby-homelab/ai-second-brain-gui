# 🧠 P.O.W.E.R-GUI

[🇺🇸 English](README.md) | [🇺🇦 Українська](README.ua.md)

[![Docker Image](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com/r/webyhomelab/power-gui)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![P.O.W.E.R](https://img.shields.io/badge/P.O.W.E.R-3.6.0-FF6B6B?style=for-the-badge)](https://github.com/weby-homelab/power-framework)
[![Tailscale](https://img.shields.io/badge/Tailscale-5F259F?style=for-the-badge&logo=tailscale&logoColor=white)](https://tailscale.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

![P.O.W.E.R-GUI Dashboard](second-brain-portal-UA.png)

![P.O.W.E.R-GUI Knowledge Graph](SB-Graph.gif)

**P.O.W.E.R-GUI** — це виробничий, AI-native веб-кокпіт та центр прийняття рішень для вашої персональної бази знань [Obsidian](https://obsidian.md) (Second Brain). Додаток розроблено виключно за стандартом **Docker-First**, він поєднує оператора-людину та автономних ШІ-агентів через екосистему **P.O.W.E.R Framework (P.A.R.A. + OKF v0.1 + Graph RAG + LLM-Wiki)**.

---

## 🏛️ Архітектура та Головні Принципи

P.O.W.E.R-GUI реалізує архітектурний патерн **Backend-For-Frontend (BFF)** на базі FastAPI та Pydantic v2 Settings. Додаток взаємодіє з базою знань виключно через канонічний інтерфейс `PowerClient` та `ApplicationService`, що гарантує повну відсутність невалідованих прямих перезаписів файлів на диску.

```
┌────────────────────────────────────────────────────────────────────────┐
│                              ОПЕРАТОР                                  │
│         (Граф знань / Гібридний пошук / Черга завдань та рішень)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / SSE (Tailscale захист)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        P.O.W.E.R-GUI (Docker)                          │
│     [Дашборд]  [Редактор нотаток]  [Task Manager v2]  [Черга рішень]   │
│     [Auth Guard] [i18n ENG/UKR]    [Темна/Світла тема] [WCAG 2.2 AA]   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ PowerClient Port
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     P.O.W.E.R Application API v2                       │
│        • Proposal Gate      • OKF Linter            • Event Ledger     │
│        • Task Store (flock) • Source Service        • Receipts Engine  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Direct / Inode I/O
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        /brain (Obsidian Vault)                         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Ключові Можливості

### 1. 🎨 Сучасна Дизайн-Система Тем (2026) та Інтернаціоналізація (i18n)
- **Lifted Dark Mode (За замовчуванням):** Глибокий графітово-синій фон (`#0b0f19`/`#131d31`) з м'якими градаціями яскравості та небесно-блакитними акцентами (`#38bdf8`).
- **Minimalist Light Mode:** Чистий фон slate-50 (`#f8fafc`), білі поверхні карток (`#ffffff`) та насичені океанічні блакитні акценти (`#0284c7`).
- **Перемикач тем `[ 🌙 | ☀️ ]`:** Миттєва зміна теми у верхній панелі навігації зі збереженням стану в cookie (`power_gui_theme`).
- **Багатомовність `[ ENG | UKR ]`:** Англійська мова встановлена базовою з можливістю швидкого перемикання на українську через панель навігації або роут `/set-lang`.

### 2. 🔒 Комплексна Безпека та Бар'єр Автентифікації
- **Обов'язковий Auth Middleware:** Неавторизований трафік до всіх приватних розділів (`/`, `/dashboard`, `/notes`, `/tasks`, `/decisions`, `/receipts`) автоматично перенаправляється на `/login` (303).
- **Константний час перевірки:** Валідація пароля через `secrets.compare_digest` із встановленням криптографічно підписаної `HttpOnly` сесійної cookie.
- **Санітизація Bleach та суворий CSP:** Повна автономність без зовнішніх CDN, захист від XSS-ін'єкцій та CSRF-атак.

### 3. 📋 Канонічний Task Manager v2 Cockpit
- **Інтерактивна Канбан-дошка:** Візуальне відстеження завдань по станах: `backlog` ➔ `ready` ➔ `in-progress` ➔ `blocked` / `input-required` / `auth-required` ➔ `completed` / `failed`.
- **Монотонний контроль ревізій:** Захист від втрати паралельних оновлень за допомогою перевірки `expected_revision`.
- **Append-Only журнал подій:** Кожна зміна стану формує незмінну подію з хешем корисного навантаження (SHA-256).
- **Живий стрімінг у реальному часі:** Миттєва доставка подій у браузер через Server-Sent Events (`/tasks/api/events/stream`).

### 4. 🛡️ Транзакційний Редактор Нотаток та Proposal Gate
- **Human-in-the-Loop потік:** ШІ-агенти та користувачі вносять зміни через пропозиції (`Edit` ➔ `Propose` ➔ `OKF Linter Validation` ➔ `Human Approval` ➔ `Apply`).
- **Захист від випадкового затирання:** Будь-яка зміна перевіряється через diff-перегляд і фіксується аудиторським чеком (Receipt).
- **Розпізнавання Obsidian Wikilinks:** Автоматичне знаходження нотаток за базовою назвою (stem, наприклад `[[Infrastructure]]`) без вказування повного шляху до підпапки.

### 5. 🌐 Динамічний 2D Граф Знань (Force-Directed)
- Візуалізація зв'язків між нотатками за допомогою D3 force-directed алгоритму.
- Підтримка глобального перегляду бази та локальних 2-рівневих піддерев для окремих документів.
- **Доступність WCAG 2.2 AA:** Таблична альтернатива з високим контрастом для екранних читачів та клавіатурної навігації.

### 6. 🔍 Мультимодальний Гібридний Пошук
- Миттєве перемикання між 4 режимами пошуку:
  - `Auto`: Гібридний щільний семантичний пошук із повнотекстовим fallback.
  - `FTS`: Швидкий повнотекстовий BM25-пошук.
  - `Semantic`: Семантичні ембеддінги (наприклад, `BGE-M3` 1024d).
  - `Reranked`: Переранжування через cross-encoder для складних запитів.

---

## 🐳 Розгортання в Docker (Основний Стандарт)

P.O.W.E.R-GUI завжди та всюди розгортається у вигляді Docker-контейнера.

### 1. Швидкий запуск однією командою

```bash
docker run -d \
  --name power-gui \
  --restart unless-stopped \
  -p 8008:8080 \
  -e POWER_GUI_AUTH_ENABLED=true \
  -e POWER_GUI_ADMIN_PASSWORD="ваш-надійний-пароль" \
  -v /шлях/до/вашого/obsidian/brain:/brain:rw \
  webyhomelab/power-gui:latest
```

Відкрийте у браузері: `http://<ip-вашого-сервера>:8008` (або адресу вашого зворотного проксі / Cloudflare Tunnel).

---

### 2. Розгортання через Docker Compose

Створіть файл `docker-compose.yml`:

```yaml
version: '3.8'

services:
  power-gui:
    image: webyhomelab/power-gui:latest
    container_name: power-gui
    restart: unless-stopped
    ports:
      - "8008:8080"
    environment:
      - POWER_GUI_HOST=0.0.0.0
      - POWER_GUI_PORT=8080
      - POWER_GUI_VAULT_PATH=/brain
      - POWER_GUI_AUTH_ENABLED=true
      - POWER_GUI_ADMIN_PASSWORD=ваш-надійний-пароль-адміністратора
      - POWER_GUI_SECRET_KEY=ваш-випадковий-секретний-ключ
      - POWER_GUI_COOKIE_SECURE=true
    volumes:
      - /шлях/до/вашого/obsidian/brain:/brain:rw
```

Запустіть сервіс:

```bash
docker compose up -d
```

---

### 3. Розгортання в Proxmox VE (LXC Контейнер `LXC 200`)

Для запуску всередині непрівілейованого контейнера Proxmox:

1. **Прокинути директорію з нотатками з хоста Proxmox у LXC:**
   ```bash
   pct set 200 -mp0 /root/geminicli/brain,mp=/mnt/brain
   ```

2. **Запустити контейнер всередині LXC з томом `/mnt/brain`:**
   ```bash
   docker run -d \
     --name power-gui \
     --restart unless-stopped \
     -p 8008:8080 \
     -e POWER_GUI_AUTH_ENABLED=true \
     -e POWER_GUI_ADMIN_PASSWORD="ваш-надійний-пароль" \
     -v /mnt/brain:/brain:rw \
     webyhomelab/power-gui:latest
   ```

---

## ⚙️ Довідник Змінних Середовища

Конфігурація здійснюється через змінні оточення з префіксом `POWER_GUI_`:

| Змінна | Тип | За замовчуванням | Опис |
| :--- | :---: | :---: | :--- |
| `POWER_GUI_HOST` | `str` | `0.0.0.0` | IP-адреса для прив'язки Uvicorn. |
| `POWER_GUI_PORT` | `int` | `8080` | Внутрішній порт сервера. |
| `POWER_GUI_VAULT_PATH` | `Path` | `/brain` | Абсолютний шлях до змонтованого ваулту Obsidian. |
| `POWER_GUI_AUTH_ENABLED` | `bool` | `true` | Обов'язкова автентифікація через сесійні кукі. |
| `POWER_GUI_ADMIN_PASSWORD` | `str` | `""` | Пароль адміністратора (перевірка у константному часі). |
| `POWER_GUI_ADMIN_PASSWORD_HASH` | `str` | `""` | Опціональний хеш пароля адміністратора (SHA256 / PBKDF2). |
| `POWER_GUI_SECRET_KEY` | `str` | `"power-secret-key-12345"` | Секретний ключ для підпису сесій та CSRF-токенів. |
| `POWER_GUI_SESSION_COOKIE_NAME` | `str` | `"power_gui_session"` | Назва сесійної cookie. |
| `POWER_GUI_SESSION_MAX_AGE_SECONDS`| `int` | `86400` | Тривалість сесії в секундах (24 години). |
| `POWER_GUI_COOKIE_SECURE` | `bool` | `false` | `true` при роботі виключно через HTTPS. |
| `POWER_GUI_COOKIE_SAMESITE` | `str` | `lax` | Політика SameSite для кукі (`lax`, `strict`, `none`). |

---

## 🧪 Тестування та Верифікація

Запуск тестів та лінтерів:

```bash
# Запуск контрактних та юніт-тестів (20+ тестів)
pytest tests/ -v

# Перевірка стилю та безпеки коду
ruff check src tests
```

---

## 📄 Ліцензія

Розповсюджується під ліцензією **MIT License**. Див. [LICENSE](LICENSE) для деталей.
