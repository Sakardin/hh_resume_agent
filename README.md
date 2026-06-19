# HH Resume Agent

Локальный агент для поиска вакансий на hh.ru через браузер, оценки совпадения с резюме через Ollama и генерации адаптированного резюме в PDF.

## Что внутри

- `data/resume_master.md` — базовое резюме
- `data/prompts.md` — цепочка промптов для разбора, переписывания и адаптации резюме
- `data/keywords.txt` — ключевые слова поиска
- `config/` — настройки из `.env`
- `browser/` — Playwright-сессия, retries, persistent profile
- `vacancies/` — поиск и парсинг вакансий hh.ru
- `llm/` — клиент Ollama и парсинг JSON-ответов
- `resume/` — оценка вакансий и адаптация резюме
- `export/` — Markdown/PDF экспорт через заменяемые интерфейсы
- `reports/` — генерация `report.json`
- `utils/` — общие утилиты
- `pipeline.py` — orchestration без привязки к CLI
- `main.py` — короткий entrypoint
- `.env.example` — пример настроек

Файлы `hh_browser.py`, `resume_agent.py` и `pdf_generator.py` оставлены как совместимые обертки над новой структурой.

## Папка `data`

В репозитории хранятся:

- `data/prompts.md` — рабочий файл с промптами для LLM, общий для проекта
- `data/resume_master.example.md` — пустой шаблон файла с основным резюме
- `data/keywords.example.txt` — пустой шаблон файла со списком поисковых запросов

Локально нужно создать свои рабочие файлы, без суффикса `.example`:

- `data/resume_master.md` — полное исходное резюме, на основе которого делается адаптация
- `data/keywords.txt` — список ключевых слов, по которым ищутся вакансии

Файл `data/prompts.md` должен быть в рабочем дереве, потому что тесты и приложение читают его напрямую.

Файлы `data/resume_master.md` и `data/keywords.txt` игнорируются Git и не должны коммититься, потому что содержат персональные данные и локальные настройки поиска.

## 1. Установить Ollama

Скачать:

```text
https://ollama.com/download
```

Проверить:

```bash
ollama --version
```

Установить модель:

```bash
ollama pull qwen3:8b
```

## 2. Подготовить Python

```bash
python -m venv venv
```

Или:

```bash
python -m venv .venv
```

## 3. Установить зависимости

```bash
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium
```

Если используется `venv`, а не `.venv`, заменить пути соответственно.

## 4. Создать `.env`

Скопировать файл:

```bash
cp .env.example .env
```

Для Windows можно просто создать копию вручную.

Настройки по умолчанию:

```env
OLLAMA_MODEL=qwen3:8b
OLLAMA_BASE_URL=http://localhost:11434/v1
LLM_DEBUG=false
LLM_LOG_PREVIEW_CHARS=800
HH_AREA=1002
MIN_MATCH_SCORE=70
MAX_RESULTS_PER_KEYWORD=10
HH_HEADLESS=false
BROWSER_PROFILE_DIR=browser_profile
PAGE_TIMEOUT_MS=60000
BROWSER_RETRY_ATTEMPTS=2
BROWSER_RETRY_DELAY_MS=1000
GENERATE_PDF=true
OUTPUT_DIR=output
SEEN_VACANCIES_PATH=output/seen_vacancies.json
RESUME_PATH=data/resume_master.md
PROMPTS_PATH=data/prompts.md
KEYWORDS_PATH=data/keywords.txt
```

`HH_AREA=1002` — Беларусь.

## 5. Запуск

В одном терминале запустить Ollama:

```bash
ollama run qwen3:8b
```

Во втором терминале:

```bash
./run.sh
```

Скрипт [run.sh](/Users/dmitry/Projects/HR-Agent/hh_resume_agent/run.sh) сам найдет `.venv` или `venv` и запустит `main.py` через Python из виртуального окружения.

Если у файла еще нет права на выполнение:

```bash
chmod +x run.sh
```

## 6. Результаты

Файлы будут в папке:

```text
output/
```

Там появятся:

- подпапка запуска с датой и временем, например `output/2026-06-17_10-45-30/`
- внутри нее адаптированные резюме `.md` с комментариями рекрутера и итоговой версией резюме
- внутри нее адаптированные резюме `.pdf`
- внутри нее `report.json`

Отдельно сохраняется файл просмотренных вакансий:

```text
output/seen_vacancies.json
```

При следующем запуске вакансии из этого списка пропускаются.

## Важно

Браузер открывается в видимом режиме. Это сделано специально. Если hh.ru покажет капчу или логин, их можно пройти вручную.

Если модель работает медленно, уменьшить:

```env
MAX_RESULTS_PER_KEYWORD=5
```

Если слишком много слабых вакансий, увеличить:

```env
MIN_MATCH_SCORE=80
```

Чтобы видеть, что приложение отправляет в Ollama, включить:

```env
LLM_DEBUG=true
```

Тогда в логах приложения будут:
- модель;
- размер prompt/response;
- укороченный preview prompt/response.

## Проверки

Быстрая проверка без запуска браузера и Ollama:

```bash
.venv/bin/python -m unittest
.venv/bin/python -m compileall -q . -x 'venv|.venv'
```
