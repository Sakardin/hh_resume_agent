# Codex Instructions

You are working on the Python project `hh_resume_agent`.

Project goal:
- search vacancies on hh.ru using Playwright;
- evaluate vacancy relevance against a resume;
- adapt the resume using a local LLM via Ollama;
- save the result as Markdown and PDF;
- continuously improve the project architecture.

## Main Rules

Write clean, professional, maintainable code.

Always split code into small executable parts:
- classes;
- services;
- functions;
- modules with clear responsibility.

Do not put all logic into `main.py`.

## Architecture

Use OOP principles and clean architecture.

Split the project into layers:

- `config` — settings and environment variables;
- `browser` — Playwright browser logic;
- `vacancies` — vacancy search and parsing;
- `llm` — Ollama / local LLM communication;
- `resume` — resume scoring and adaptation;
- `export` — Markdown/PDF export;
- `reports` — reports;
- `utils` — shared helper functions.

## Best Practices

Follow these rules:

- Single Responsibility Principle;
- Dependency Injection where useful;
- clear class, method, and variable names;
- type hints everywhere practical;
- `dataclass` or Pydantic models for structured data;
- clear custom exceptions where needed;
- logging instead of random `print` calls;
- configuration only through `.env` or a config class;
- do not commit personal data;
- do not store resumes, prompts, generated PDFs, or browser profiles in git.

## Playwright

Playwright code must be resilient.

Add:
- proper element waits;
- retry logic;
- handling for the `Try again` / `Попробовать снова` button;
- persistent browser profile support;
- protection against empty pages;
- clear errors when a vacancy cannot be opened.

Do not rely on fragile selectors without fallbacks.

## LLM

Keep LLM logic isolated.

Required responsibilities:
- vacancy match scoring;
- resume adaptation;
- JSON response parsing;
- LLM response validation;
- preventing the model from inventing experience.

## PDF and Export

PDF generation must be replaceable.

Do not hard-bind the whole project to WeasyPrint.

Create exporter abstractions:

- `MarkdownExporter`;
- `PdfExporter`;
- later `DocxExporter`.

## main.py

`main.py` must stay short.

It should only:
- load config;
- create dependencies;
- run the pipeline.

All business logic must live in classes and services.

## Testability

Write code so it can be tested.

Prefer adding:
- unit tests;
- mocks for Playwright;
- mocks for LLM;
- vacancy parsing tests;
- report generation tests.

## Before Large Changes

Before a large refactor:

1. inspect the current structure;
2. propose a short plan;
3. apply changes in small steps.

## After Changes

After changes, check:

```bash
python main.py
```
