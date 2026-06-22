# HH Resume Agent

Локальный агент для поиска вакансий на hh.ru через браузер, оценки совпадения с резюме через Ollama и генерации адаптированного резюме в Markdown.

## Что внутри

- `data/resume_master.md` — базовое резюме
- `data/prompts.md` — цепочка промптов для разбора, переписывания и адаптации резюме
- `data/keywords.txt` — ключевые слова поиска
- `config/` — настройки из `.env`
- `browser/` — Playwright-сессия, retries, persistent profile
- `vacancies/` — поиск и парсинг вакансий hh.ru
- `llm/` — клиент Ollama и парсинг JSON-ответов
- `resume/` — оценка вакансий и адаптация резюме
- `export/` — экспорт через заменяемые интерфейсы
- `reports/` — генерация `report.json`, `report.html` и helper-скриптов
- `utils/` — общие утилиты
- `pipeline.py` — orchestration без привязки к CLI
- `main.py` — короткий entrypoint
- `.env.example` — пример настроек

Файлы `hh_browser.py` и `resume_agent.py` оставлены как совместимые обертки над новой структурой.

## Папка `data`

В репозитории хранятся:

- `data/resume_master.example.md` — шаблон файла с основным резюме
- `data/prompts.md` — рабочий файл с промптами для LLM, общий для проекта
- `data/keywords.example.txt` — шаблон файла со списком поисковых запросов

Локально нужно создать свои рабочие файлы, без суффикса `.example`:

- `data/resume_master.md` — полное исходное резюме, на основе которого делается адаптация
- `data/keywords.txt` — список ключевых слов, по которым ищутся вакансии

Проще всего создать их так:

```bash
cp data/resume_master.example.md data/resume_master.md
cp data/keywords.example.txt data/keywords.txt
```

После этого заполнить:

- `data/resume_master.md` своим резюме
- `data/keywords.txt` своими поисковыми запросами, по одному на строку

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

Запустить Ollama API:

```bash
ollama serve
```

По умолчанию проект обращается к:

```text
http://localhost:11434/v1
```

Проверить, что сервер Ollama поднят:

```bash
curl http://localhost:11434/api/tags
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
GENERATE_RESUME_ON_MATCH=false
OUTPUT_DIR=output
SEEN_VACANCIES_PATH=output/seen_vacancies.json
RESUME_PATH=data/resume_master.md
PROMPTS_PATH=data/prompts.md
KEYWORDS_PATH=data/keywords.txt
```

`HH_AREA=1002` — Беларусь.

## 5. Запуск

В одном терминале запустить Ollama API:

```bash
ollama serve
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
- внутри нее `report.json`
- внутри нее `report.html`
- внутри нее helper-скрипты `generate_resume_*.command`
- после генерации из `report.html` внутри той же папки появятся адаптированные резюме `.md` с комментариями рекрутера и итоговой версией резюме

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

По умолчанию резюме не генерируются во время основного прогона. Для этого отчет сначала собирает только score, reason, strong matches и gaps.

Если нужно генерировать резюме сразу для каждой подходящей вакансии, включить:

```env
GENERATE_RESUME_ON_MATCH=true
```

## Проверки

Быстрая проверка без запуска браузера и Ollama:

```bash
.venv/bin/python -m unittest
.venv/bin/python -m compileall -q . -x 'venv|.venv'
```
