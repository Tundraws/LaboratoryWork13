# PROMPT_LOG.md

## Использованные AI-инструменты

- Codex в режиме senior software engineer / архитектор учебных production-like проектов.
- Локальные инструменты проверки: `go test`, `pytest`, `go mod tidy`.

## Исходный промпт

Пользователь попросил реализовать лабораторную работу №13 по теме «Мультиагентные системы» для варианта 13 повышенной сложности: анализ социальных сетей. Требования включали исходный код в `src/`, тесты в `tests/`, README на русском языке, `PROMPT_LOG.md`, Docker Compose, чистую архитектуру, Go-агентов, Python-оркестратор, NATS, Redis, трассировку, retry/timeout, веб-панель и понятную историю коммитов.

## Что сгенерировано

- Универсальный Go-агент с конфигурацией ролей через JSON.
- Четыре роли агентов: сбор постов, анализ тональности, выявление трендов, генерация отчётов.
- Python/FastAPI-оркестратор с pipeline, auction bidding, retry и timeout.
- JWT-проверка для запуска анализа.
- Dashboard для просмотра событий и технической трассировки.
- Docker Compose с NATS, Redis, Jaeger, оркестратором и четырьмя агентами.
- Unit-тесты Go и Python.
- README с инструкциями по сборке, запуску, API и архитектурой.

## Проблемы во время генерации

- Репозиторий на GitHub был пустым, поэтому проект создавался с нуля.
- `go mod tidy` сначала не смог записать build cache из-за sandbox-ограничений. Команда была повторена с разрешением.
- В Go fallback Redis -> memory store сначала имел конкретный тип `*RedisStore`, что мешало подставить `*MemoryStore`. Исправлено через интерфейс `state.Store`.
- Локальная среда использовала Python 3.13, а старый pin Pydantic 2.7 пытался собрать несовместимый `pydantic-core`. Версии FastAPI/Pydantic были обновлены до совместимых с Python 3.13.
- Pytest сначала не видел пакет `social_mas` из корневой директории. Добавлен корневой `pytest.ini` с `pythonpath = src/orchestrator/src`.

## Что исправлялось вручную после генерации

- Добавлен `go.sum` через `go mod tidy`.
- Обновлены Python-зависимости.
- Добавлен `PYTHONPATH=/app/src` в Dockerfile оркестратора.
- Добавлены отдельные тесты validation/security и retry/timeout.
- Добавлены русскоязычные инструкции и примеры команд.

## Найденные runtime issues

- Ошибка компиляции Go из-за несовместимого типа state store.
- Ошибка установки Python-зависимостей из-за несовместимости `pydantic-core` с Python 3.13.
- Ошибка импорта Python-пакета в тестах без явного `pythonpath`.

## Улучшения после проверки

- Go-тесты успешно проходят: `go test ./...`.
- Python-тесты успешно проходят: `pytest tests\python`.
- Проект получил атомарные Conventional Commits:
  - `feat: scaffold social media mas project`
  - `fix: make go agent compile with fallback state`
  - `test: configure python test dependencies`
  - последующие коммиты документации и финальной полировки.

