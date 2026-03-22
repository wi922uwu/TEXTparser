# OCR Web Service

Инструмент распознавания текста и таблиц из сканированных документов для изолированной корпоративной среды.

## Возможности

- ✓ Распознавание русского и латинского текста
- ✓ Извлечение таблиц с сохранением структуры
- ✓ Поддержка форматов: PDF, JPG, PNG, TIFF
- ✓ Экспорт: TXT, DOCX, XLSX, CSV
- ✓ Пакетная обработка файлов
- ✓ Полная автономность (без внешних API)

## Технологии

- **Backend:** FastAPI + PaddleOCR
- **Frontend:** React + TypeScript
- **Очередь:** Celery + Redis
- **Развертывание:** Docker + Docker Compose

## Быстрый старт

### 1. Загрузка моделей

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python ../scripts/download_models.py
```

### 2. Запуск с Docker

```bash
docker-compose up
```

Откройте http://localhost в браузере.

## Документация

- [Инструкция по установке](docs/installation.md)
- [Руководство пользователя](docs/user-guide.md)
- [Развертывание](docs/deployment.md)

## Требования

- Python 3.11+
- Node.js 20+
- Docker 24.0+
- Redis 7.2+
- Минимум 4GB RAM (рекомендуется 8GB+)

## Лицензия

Для внутреннего использования.
