# Архитектура OCR Web Service

## Обзор системы

OCR Web Service — это веб-приложение для распознавания текста и таблиц из сканированных документов, работающее в изолированной корпоративной среде.

## Компоненты системы

### 1. Frontend (React + TypeScript)

**Технологии:**
- React 18.2
- TypeScript 5.3
- Vite (сборщик)
- Axios (HTTP клиент)
- React Dropzone (загрузка файлов)

**Основные компоненты:**
- `FileUpload` — загрузка файлов (drag-and-drop)
- `ProcessingQueue` — отображение очереди обработки
- `Results` — отображение и скачивание результатов

**Взаимодействие:**
- REST API для загрузки файлов и запуска обработки
- Polling для отслеживания статуса задач (каждые 2 секунды)

### 2. Backend (FastAPI)

**Технологии:**
- FastAPI 0.109
- Uvicorn (ASGI сервер)
- Pydantic (валидация данных)

**API Endpoints:**
```
POST   /api/v1/upload        - Загрузка одного файла
POST   /api/v1/upload/batch  - Пакетная загрузка
POST   /api/v1/process       - Запуск обработки
GET    /api/v1/status/{id}   - Статус задачи
GET    /api/v1/result/{id}   - Скачивание результата
GET    /api/v1/health        - Проверка здоровья
```

**Модули:**
- `api/` — REST API endpoints
- `core/` — OCR движок и обработка
- `exporters/` — экспорт в форматы
- `tasks/` — Celery задачи
- `storage/` — управление файлами

### 3. OCR Engine (PaddleOCR)

**Компоненты:**

#### ocr_engine.py
- Инициализация PaddleOCR с русским языком
- Распознавание текста из изображений
- Определение таблиц (PP-Structure)

#### preprocessor.py
- Коррекция наклона (deskew)
- Улучшение контраста (CLAHE)
- Бинаризация (adaptive thresholding)
- Шумоподавление

#### table_detector.py
- Определение структуры таблиц
- Извлечение ячеек
- Обнаружение объединенных ячеек
- Определение заголовков

#### text_extractor.py
- Группировка текста по блокам
- Сортировка в порядке чтения
- Формирование параграфов

### 4. Exporters

**Форматы экспорта:**

#### TXT (txt_exporter.py)
- Простой текст с сохранением структуры
- Таблицы в виде tab-separated values

#### DOCX (docx_exporter.py)
- Форматированный документ Word
- Таблицы с сохранением структуры
- Параграфы и заголовки

#### XLSX (xlsx_exporter.py)
- Таблицы Excel
- Объединенные ячейки
- Форматирование заголовков
- Автоматическая ширина столбцов

#### CSV (csv_exporter.py)
- UTF-8 с BOM (для Excel)
- Первая таблица из документа

### 5. Task Queue (Celery + Redis)

**Celery:**
- Асинхронная обработка OCR задач
- Отслеживание прогресса
- Обработка ошибок и повторные попытки

**Redis:**
- Брокер сообщений для Celery
- Backend для хранения результатов
- Кэширование (опционально)

**Задачи:**
- `process_document` — основная задача OCR
- `cleanup_old_files` — очистка старых файлов

### 6. Nginx (Reverse Proxy)

**Функции:**
- Проксирование запросов к backend
- Раздача статических файлов frontend
- Балансировка нагрузки (при масштабировании)
- SSL/TLS терминация (в production)

## Поток данных

### Загрузка и обработка

```
1. Пользователь загружает файл
   ↓
2. Frontend → POST /api/v1/upload
   ↓
3. Backend сохраняет файл → FileManager
   ↓
4. Frontend → POST /api/v1/process
   ↓
5. Backend создает Celery задачу
   ↓
6. Celery Worker:
   - Загружает файл
   - Конвертирует PDF → изображения (если нужно)
   - Предобработка изображений
   - OCR распознавание (PaddleOCR)
   - Извлечение текста и таблиц
   - Экспорт в форматы
   ↓
7. Frontend polling → GET /api/v1/status/{task_id}
   ↓
8. Пользователь скачивает результаты
```

### Обработка одной страницы

```
Изображение
   ↓
Preprocessor (deskew, enhance, binarize)
   ↓
OCR Engine (PaddleOCR)
   ↓
┌─────────────┬──────────────┐
│             │              │
Text Extractor  Table Detector
│             │              │
└─────────────┴──────────────┘
   ↓
Structured Data
   ↓
Exporters (TXT, DOCX, XLSX, CSV)
   ↓
Result Files
```

## Хранение данных

### Файловая система

```
/app/
├── uploads/          # Загруженные файлы
│   └── {file_id}/
│       └── original.{ext}
├── results/          # Результаты обработки
│   └── {file_id}/
│       ├── result.txt
│       ├── result.docx
│       ├── result.xlsx
│       └── result.csv
└── models/           # Модели PaddleOCR
    ├── det/
    ├── rec/
    ├── cls/
    └── table/
```

### Redis

```
celery:              # Очередь задач
celery-task-meta-*:  # Метаданные задач
```

## Безопасность

### Изоляция

1. **Сетевая изоляция:**
   - Все сервисы в Docker network
   - Только Nginx доступен извне (порт 80/443)

2. **Отсутствие внешних подключений:**
   - Модели PaddleOCR предзагружены
   - Нет API вызовов во внешние сервисы
   - Полная автономность

3. **Валидация:**
   - Проверка типов файлов
   - Ограничение размера (50MB)
   - Санитизация имен файлов

4. **Временное хранение:**
   - Автоматическое удаление через 24 часа
   - Периодическая очистка (cleanup task)

## Масштабирование

### Горизонтальное масштабирование

```yaml
# Увеличение Celery workers
celery-worker:
  deploy:
    replicas: 4
```

### Вертикальное масштабирование

```yaml
# Увеличение ресурсов
celery-worker:
  deploy:
    resources:
      limits:
        cpus: '4.0'
        memory: 8G
```

### Балансировка нагрузки

```
       ┌─────────┐
       │  Nginx  │
       └────┬────┘
            │
    ┌───────┼───────┐
    │       │       │
┌───▼──┐ ┌──▼──┐ ┌─▼───┐
│Worker│ │Worker│ │Worker│
└──────┘ └─────┘ └─────┘
```

## Мониторинг

### Метрики

- Количество задач в очереди
- Время обработки документов
- Использование CPU/RAM
- Размер хранилища

### Логирование

```python
# Уровни логирования
DEBUG   - Детальная отладочная информация
INFO    - Общая информация о работе
WARNING - Предупреждения
ERROR   - Ошибки обработки
```

### Health Checks

```bash
# API health
GET /api/v1/health

# Docker health
docker-compose ps

# Redis health
docker exec ocr-redis redis-cli ping
```

## Производительность

### Оптимизации

1. **Кэширование моделей:**
   - Модели PaddleOCR загружаются один раз
   - Хранятся в памяти worker процесса

2. **Параллельная обработка:**
   - Несколько Celery workers
   - Асинхронная обработка задач

3. **Предобработка:**
   - Улучшение качества изображений
   - Повышение точности OCR

4. **Оптимизация изображений:**
   - Resize больших изображений
   - Конвертация в оптимальный формат

### Узкие места

1. **OCR обработка:**
   - Самая медленная операция
   - ~20-30 секунд на страницу

2. **PDF конвертация:**
   - Для многостраничных PDF
   - ~1-2 секунды на страницу

3. **Экспорт:**
   - Быстрая операция
   - <1 секунда для всех форматов

## Технологический стек

### Backend
- Python 3.11
- FastAPI 0.109
- PaddleOCR 2.7
- Celery 5.3
- Redis 5.0

### Frontend
- React 18.2
- TypeScript 5.3
- Vite 5.0
- Axios 1.6

### Infrastructure
- Docker 24.0
- Docker Compose 2.24
- Nginx 1.25
- Redis 7.2

### Libraries
- OpenCV (предобработка)
- PyMuPDF (PDF обработка)
- python-docx (DOCX экспорт)
- openpyxl (XLSX экспорт)
- Pillow (обработка изображений)

## Развертывание

### Development
```bash
# Backend
uvicorn app.main:app --reload

# Frontend
npm run dev

# Redis
redis-server

# Celery
celery -A app.tasks.celery_app worker
```

### Production
```bash
# Docker Compose
docker-compose up -d
```

## Будущие улучшения

1. **WebSocket для real-time обновлений**
2. **GPU поддержка для ускорения OCR**
3. **Batch API для массовой обработки**
4. **Кэширование результатов**
5. **Метрики и дашборды (Prometheus + Grafana)**
6. **Поддержка дополнительных языков**
7. **Улучшенное распознавание таблиц**
8. **API для интеграции с другими системами**
