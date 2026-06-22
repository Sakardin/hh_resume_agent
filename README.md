# HH Resume Agent

Локальный агент для поиска вакансий на `hh.ru`, оценки их релевантности по резюме и генерации адаптированного резюме через локальную LLM.

Проект работает в двух режимах:

- основной прогон ищет вакансии, считает `score`, `reason`, `strong_matches`, `gaps` и сохраняет отчет;
- генерация резюме делается по запросу из `report.html` или через CLI-команду `generate`.

## Что внутри

- `config/` — загрузка настроек из `.env`
- `browser/` — Playwright-сессия, retries, persistent profile
- `vacancies/` — поиск и парсинг вакансий HH
- `llm/` — клиент OpenAI-compatible API для Ollama / LM Studio
- `resume/` — скоринг вакансий и адаптация резюме
- `export/` — Markdown/PDF экспорт
- `reports/` — `report.json`, `report.html`, HTML preview и helper-скрипты
- `utils/` — общие утилиты
- `pipeline.py` — основной orchestration
- `main.py` — короткий entrypoint
- `cli.py` — CLI-команды

Совместимые обертки `hh_browser.py`, `resume_agent.py` и `pdf_generator.py` сохранены, но основной путь запуска идет через `main.py`.

## Подготовить данные

В репозитории есть шаблоны:

- `data/resume_master.example.md`
- `data/keywords.example.txt`
- `data/prompts.md`

Нужно создать локальные рабочие файлы:

```bash
cp data/resume_master.example.md data/resume_master.md
cp data/keywords.example.txt data/keywords.txt
```

После этого заполнить:

- `data/resume_master.md` своим базовым резюме
- `data/keywords.txt` поисковыми запросами, по одному на строку

Файлы `data/resume_master.md` и `data/keywords.txt` игнорируются Git.

## LLM Backend

Проект использует OpenAI-compatible HTTP API. Подходит:

- `Ollama`
- `LM Studio`

### Вариант 1: Ollama

Установить Ollama:

```text
https://ollama.com/download
```

Проверить:

```bash
ollama --version
```

Скачать модель:

```bash
ollama pull qwen3:8b
```

Запустить API:

```bash
ollama serve
```

По умолчанию проект ожидает endpoint:

```text
http://localhost:11434/v1
```

Проверить, что сервер поднят:

```bash
curl http://localhost:11434/api/tags
```

### Вариант 2: LM Studio

Если Ollama не используется, можно работать через `LM Studio`.

Что сделать:

1. Установить и открыть `LM Studio`
2. Скачать локальную instruct/chat модель
3. Загрузить модель в память
4. Открыть `Developer` -> `Local Server`
5. Запустить OpenAI-compatible endpoint

Обычно `LM Studio` поднимает API по адресу:

```text
http://127.0.0.1:1234/v1
```

В этом случае в `.env` надо заменить:

```env
OLLAMA_BASE_URL=http://127.0.0.1:1234/v1
OLLAMA_MODEL=<имя_модели_из_LM_Studio>
```

Пример:

```env
OLLAMA_BASE_URL=http://127.0.0.1:1234/v1
OLLAMA_MODEL=qwen2.5-7b-instruct
```

Если используется `LM Studio`, команды `ollama pull` и `ollama serve` не нужны.

## Python и зависимости

Создать виртуальное окружение:

```bash
python -m venv .venv
```

Установить зависимости:

```bash
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium
```

Если используется `venv`, а не `.venv`, заменить пути соответственно.

## Настроить `.env`

Создать `.env`:

```bash
cp .env.example .env
```

Текущие настройки по умолчанию:

```env
OLLAMA_MODEL=qwen3:8b
OLLAMA_BASE_URL=http://localhost:11434/v1
LLM_DEBUG=false
LLM_LOG_PREVIEW_CHARS=800
MIN_MATCH_SCORE=70
MAX_RESULTS_PER_KEYWORD=10
SEARCH_PAGES_PER_KEYWORD=5
HH_HEADLESS=false
BROWSER_PROFILE_DIR=browser_profile
PAGE_TIMEOUT_MS=60000
BROWSER_RETRY_ATTEMPTS=2
BROWSER_RETRY_DELAY_MS=1000
GENERATE_PDF=true
GENERATE_RESUME_ON_MATCH=false
OPEN_REPORT_IN_BROWSER=true
OUTPUT_DIR=output
SEEN_VACANCIES_PATH=output/seen_vacancies.json
RESUME_PATH=data/resume_master.md
PROMPTS_PATH=data/prompts.md
KEYWORDS_PATH=data/keywords.txt
```

Дополнительно:

- `HH_AREA` можно задать вручную, если нужен фильтр по региону, например `HH_AREA=1002`
- `SEARCH_PAGES_PER_KEYWORD=5` задает, сколько страниц выдачи HH просматривать по каждому запросу
- `GENERATE_RESUME_ON_MATCH=false` означает, что резюме не генерируется в основном прогоне, а создается по запросу из отчета
- `OPEN_REPORT_IN_BROWSER=true` включает автoоткрытие `report.html` после завершения

## Запуск на macOS / Linux

В одном терминале запустить LLM backend:

- для Ollama: `ollama serve`
- для LM Studio: просто поднять `Local Server`

Во втором терминале:

```bash
./run.sh
```

Скрипт [run.sh](/Users/dmitry/Projects/HR-Agent/hh_resume_agent/run.sh) сам найдет `.venv` или `venv`, проверит обязательные локальные файлы и запустит `main.py`.

Если у `run.sh` нет права на выполнение:

```bash
chmod +x run.sh
```

## Запуск в Windows

В Windows `run.sh` не нужен.

Создать виртуальное окружение:

```powershell
python -m venv .venv
```

Установить зависимости:

```powershell
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\playwright install chromium
```

Подготовить локальные файлы:

```powershell
copy data\resume_master.example.md data\resume_master.md
copy data\keywords.example.txt data\keywords.txt
copy .env.example .env
```

Запустить LLM backend:

- для Ollama: `ollama serve`
- для LM Studio: поднять `Local Server`

Запустить основной прогон:

```powershell
.venv\Scripts\python main.py
```

## Что делает основной прогон

По умолчанию проект:

1. читает `resume_master.md`, `prompts.md`, `keywords.txt`
2. ищет вакансии на HH
3. пропускает уже просмотренные вакансии из `output/seen_vacancies.json`
4. считает `score`, `strong_matches`, `gaps`, `reason`
5. для вакансий выше порога пишет отчет

Если включить:

```env
GENERATE_RESUME_ON_MATCH=true
```

то резюме будет генерироваться сразу во время основного прогона.

## Результаты

Файлы сохраняются в:

```text
output/
```

Для каждого запуска создается отдельная папка, например:

```text
output/2026-06-22_18-40-00/
```

Внутри нее будут:

- `report.json`
- `report.html`
- `generate_resume_*.command` helper-скрипты для генерации резюме по вакансии
- `.md` файлы адаптированных резюме, если генерация уже выполнялась
- `.resume.html` preview для сгенерированных Markdown-файлов
- `.pdf`, если `GENERATE_PDF=true` и WeasyPrint смог отработать

Отдельно сохраняется:

```text
output/seen_vacancies.json
```

## Как сгенерировать резюме после основного прогона

Есть два варианта.

### Вариант 1: из `report.html`

Открыть `report.html` и нажать `Generate Resume` у нужной вакансии.

После генерации отчет и ссылки на артефакты обновятся.

### Вариант 2: через CLI

macOS / Linux:

```bash
./run.sh generate --report-dir output/YYYY-MM-DD_HH-MM-SS --vacancy-url "https://hh.ru/vacancy/123456"
```

Windows:

```powershell
.venv\Scripts\python main.py generate --report-dir output\YYYY-MM-DD_HH-MM-SS --vacancy-url "https://hh.ru/vacancy/123456"
```

## Важно

- Браузер по умолчанию запускается не в headless-режиме, чтобы можно было вручную пройти капчу или логин
- Если модель работает медленно, уменьшить `MAX_RESULTS_PER_KEYWORD`
- Если слишком много слабых вакансий, увеличить `MIN_MATCH_SCORE`
- Если нужен полный лог запросов к модели, включить `LLM_DEBUG=true`

## Проверки

Быстрые локальные проверки:

```bash
.venv/bin/python -m unittest
.venv/bin/python main.py --help
```
