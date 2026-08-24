# Human Design API — Инструкция по установке на Ubuntu

## Что изменено относительно оригинального репозитория

- **pytz заменён на zoneinfo + tzdata** — встроенный модуль Python 3.9+, не требует внешних зависимостей
- Обновлены файлы: `features/core.py`, `requirements.txt`, `pyproject.toml`
- Добавлен `setup_ubuntu.sh` — скрипт автоматической установки
- Обновлён `Dockerfile` (healthcheck, локальная сборка)
- Обновлён `docker-compose.yml` (локальная сборка вместо внешнего образа)

---

## Вариант 1: Автоматическая установка (рекомендуется)

```bash
cd ASTRO
chmod +x setup_ubuntu.sh
./setup_ubuntu.sh
```

Скрипт сам установит системные пакеты, создаст venv, поставит зависимости и проверит что всё работает.

После установки:

```bash
source venv/bin/activate
uvicorn humandesign.api:app --host 0.0.0.0 --port 9021 --reload
```

---

## Вариант 2: Ручная установка

### 1. Системные пакеты

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-dev python3-pip gcc g++ git
```

### 2. Виртуальное окружение

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Зависимости

```bash
pip install -r requirements.txt
pip install -e .
```

### 4. Настройка .env

```bash
cp .env_example .env
# Отредактируй .env — задай токен:
# HD_API_TOKEN=твой_секретный_токен
```

### 5. Запуск

```bash
uvicorn humandesign.api:app --host 0.0.0.0 --port 9021 --reload
```

---

## Вариант 3: Docker

```bash
docker-compose up --build -d
```

API будет на http://localhost:9021

---

## Проверка работы

Swagger UI: http://localhost:9021/docs

Тестовый запрос:
```bash
curl "http://localhost:9021/calculate?year=1990&month=7&day=15&hour=14&minute=30&place=London" \
     -H "Authorization: Bearer dev_token_12345"
```

Тесты:
```bash
pytest tests/ -v
```

---

## Структура проекта (ключевые файлы)

| Файл | Что делает |
|------|-----------|
| `src/humandesign/api.py` | Точка входа FastAPI, подключает роутеры |
| `src/humandesign/features/core.py` | Ядро расчётов HD (Swiss Ephemeris) |
| `src/humandesign/features/mechanics.py` | Тип, авторитет, каналы, определённость |
| `src/humandesign/features/attributes.py` | Профиль, Крест Инкарнации, переменные |
| `src/humandesign/hd_constants.py` | Константы HD (ворота, каналы, кресты) |
| `src/humandesign/routers/general.py` | Эндпоинты /health и /calculate |
| `src/humandesign/routers/v2/general.py` | Эндпоинт /v2/calculate |
| `src/humandesign/routers/analyze.py` | Эндпоинты /analyze/composite, /penta, /wa, /maia-penta |
| `src/humandesign/routers/admin.py` | Эндпоинты /admin/sites и /admin/stats |
| `src/humandesign/routers/panel.py` | Веб-панель оператора /panel/* |
| `src/humandesign/relational/` | Диада, композит, Пента и WA (заменил services/composite.py) |
| `src/humandesign/services/geolocation.py` | Геокодирование (Nominatim + TimezoneFinder) |
| `src/humandesign/services/enrichment.py` | Справка по воротам, линиям и каналам из hd_data.sqlite |

Модулей `routers/transits.py`, `routers/composite.py`, `services/composite.py` и
`services/chart_renderer.py` в проекте нет — они были удалены. Эндпоинтов
`/transits/*` и `/bodygraph` не существует.

---

## Зависимости и их назначение

| Библиотека | Зачем |
|-----------|-------|
| **pysweph** | Swiss Ephemeris — положения планет (C-расширение) |
| **fastapi** | Веб-фреймворк API |
| **uvicorn** | ASGI-сервер |
| **pydantic** | Валидация данных |
| **geopy** | Геокодирование (город → координаты) через Nominatim |
| **timezonefinder** | Координаты → часовой пояс |
| **tzdata** | База данных часовых поясов для zoneinfo |
| **numpy / pandas** | Математика и данные |
| **matplotlib / svgpath2mpl / Pillow** | Рендеринг бодиграфа |
| **python-dateutil** | Работа с датами |
| **httpx / pytest** | Тестирование |

---

## Эфемериды Swiss Ephemeris и точность расчётов

### Три режима работы

Swiss Ephemeris поддерживает три источника данных (автоматически выбирает лучший доступный):

| Режим | Точность | Размер | Диапазон |
|-------|---------|--------|----------|
| **Swiss Ephemeris `.se1`** (сжатый JPL DE431) | 0.001" (миллисекунда дуги) | ~2 МБ на 600 лет | 13000 BCE – 17000 CE |
| Оригинальный JPL DE431 | 0.001" | 2.6 ГБ | 13000 BCE – 17000 CE |
| Moshier (встроенный fallback) | ~0.1" планеты, ~3" Луна | 0 (встроен в pysweph) | 3000 BCE – 3000 CE |

### Что включено в этот пакет

В папке `ephe/` находятся сжатые файлы Swiss Ephemeris на основе JPL DE431, покрывающие 1800–2399 CE:

| Файл | Содержимое | Размер |
|------|-----------|--------|
| `sepl_18.se1` | Планеты (Солнце–Плутон) | 473 КБ |
| `semo_18.se1` | Луна | 1.3 МБ |
| `seas_18.se1` | Основные астероиды | 218 КБ |
| `sefstars.txt` | Неподвижные звёзды | 134 КБ |

Этого достаточно для расчётов HD для людей, родившихся с 1800 по 2399 год (с учётом design date -88° Солнца ≈ 3 месяца до рождения).

### Как работает автоматический выбор

Код автоматически ищет эфемериды в таком порядке:
1. Переменная окружения `SE_EPHE_PATH` (если задана)
2. Папка `ephe/` в корне проекта
3. Если файлы не найдены — Moshier (встроенный)

### Проверка режима

После запуска API проверь эндпоинт `/health`:
```bash
curl http://localhost:9021/health
```
В поле `dependencies.pysweph` будет указано:
- `"ready (Swiss Ephemeris / DE431)"` — файлы `.se1` подключены
- `"ready (Moshier)"` — fallback, файлы не найдены

### Расширение диапазона

Для расчётов за пределами 1800–2399 скачай дополнительные файлы из [репозитория Swiss Ephemeris](https://github.com/aloistr/swisseph/tree/master/ephe) и положи в `ephe/`:
```bash
# Пример: добавить покрытие 1200–1799
cd ephe/
wget https://github.com/aloistr/swisseph/raw/master/ephe/sepl_12.se1
wget https://github.com/aloistr/swisseph/raw/master/ephe/semo_12.se1
```
