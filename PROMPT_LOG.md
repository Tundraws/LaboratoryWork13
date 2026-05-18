# PROMPT_LOG.md

## Использованные AI-инструменты

- Codex в режиме senior software engineer / архитектор учебных production-like проектов.
- Локальные инструменты проверки: `go test`, `pytest`, `go mod tidy`, `docker compose config`, `docker compose build`.

## Исходный промпт

Пользователь попросил реализовать лабораторную работу №13 по теме «Мультиагентные системы» для варианта 13 повышенной сложности: анализ социальных сетей. Требования включали исходный код в `src/`, тесты в `tests/`, README на русском языке, `PROMPT_LOG.md`, Docker Compose, чистую архитектуру, Go-агентов, Python-оркестратор, NATS, Redis, трассировку, retry/timeout, веб-панель и понятную историю коммитов.

## Что сгенерировано

- Универсальный Go-агент с конфигурацией ролей через JSON.
- Четыре Go-роли: сбор постов, анализ тональности, выявление трендов, генерация отчётов.
- Отдельный Python LLM-агент с поддержкой Ollama, cloud-compatible API и deterministic fallback без секретов.
- Python/FastAPI-оркестратор с pipeline, auction bidding, retry и timeout.
- JWT-проверка для запуска анализа.
- Dashboard для просмотра событий и технической трассировки.
- Docker Compose с NATS, Redis, Jaeger, оркестратором, четырьмя Go-агентами и Python LLM-агентом.
- Unit-тесты Go и Python.
- README с инструкциями по сборке, запуску, API и архитектурой.

## Проблемы во время генерации

- Репозиторий на GitHub был пустым, поэтому проект создавался с нуля.
- `go mod tidy` сначала не смог записать build cache из-за sandbox-ограничений. Команда была повторена с разрешением.
- В Go fallback Redis -> memory store сначала имел конкретный тип `*RedisStore`, что мешало подставить `*MemoryStore`. Исправлено через интерфейс `state.Store`.
- Локальная среда использовала Python 3.13, а старый pin Pydantic 2.7 пытался собрать несовместимый `pydantic-core`. Версии FastAPI/Pydantic были обновлены до совместимых с Python 3.13.
- Pytest сначала не видел пакет `social_mas` из корневой директории. Добавлен корневой `pytest.ini`.
- После первой автоматической проверки Telegram-бот указал критический дефект: отсутствовал отдельный LLM-агент для задания 7 повышенной сложности.

## Что исправлялось вручную после генерации

- Добавлен `go.sum` через `go mod tidy`.
- Обновлены Python-зависимости.
- Добавлен `PYTHONPATH=/app/src` в Dockerfile оркестратора.
- Добавлен `src/llm-agent` как самостоятельный Python-сервис, подключённый к NATS и `docker-compose.yml`.
- Pipeline расширен шагом `collector -> sentiment -> trends -> llm -> reports`.
- Добавлены отдельные тесты validation/security, retry/timeout и LLM prompt/provider.
- Добавлены русскоязычные инструкции и примеры команд.

## Найденные runtime issues

- Ошибка компиляции Go из-за несовместимого типа state store.
- Ошибка установки Python-зависимостей из-за несовместимости `pydantic-core` с Python 3.13.
- Ошибка импорта Python-пакета в тестах без явного `pythonpath`.
- Автопроверка не засчитала задание 7 из-за отсутствия LLM-сервиса. Исправлено добавлением Python LLM-агента и документации.

## Улучшения после проверки

- Go-тесты успешно проходят: `go test ./...`.
- Python-тесты успешно проходят: `pytest tests\python`.
- Docker Compose содержит сервис `llm-agent`, а README описывает режимы `mock`, `ollama` и `cloud`.
- Проект получил атомарные Conventional Commits:
  - `feat: scaffold social media mas project`
  - `fix: make go agent compile with fallback state`
  - `test: configure python test dependencies`
  - `docs: add lab instructions and prompt log`
  - `feat: add python llm insight agent`

