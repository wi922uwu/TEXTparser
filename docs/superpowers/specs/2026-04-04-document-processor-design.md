# Document Processor — Design Spec

**Дата:** 2026-04-04
**Статус:** Draft

## Контекст

Требуется веб-приложение для извлечения текста и таблиц из документов с максимальной точностью.
Работает полностью локально (open source, без внешних API).
Кроссплатформенность через веб-интерфейс (Windows + Linux).

## Требования

1. Загрузка: PDF, JPG, PNG, TIFF (включая многостраничные)
2. Выбор формата выгрузки: TXT, DOCX (текст), XLSX (таблицы)
3. Время обработки: ≤30 сек/документ (макс. 1 мин)
4. Скачивание результатов
5. **Максимальная точность** OCR
6. Без внешних API — полностью локальная обработка
7. Docker-развёртывание

## Архитектура

### Backend — Python (FastAPI)

```
backend/
├── main.py              — FastAPI app, маршруты
├── config.py            — конфигурация
├── pipeline.py          — оркестрация пайплайна
├── models/
│   └── schemas.py       — Pydantic модели
├── ocr/
│   ├── tesseract.py     — Tesseract 5 OCR
│   ├── surya.py         — Surya OCR для сложных документов
│   ├── table.py         — Table Transformer для таблиц
│   └── engine.py        — комбинированный движок
├── preprocess/
│   └── image.py         — denoise, deskew, contrast, binarization
└── export/
    ├── text.py          — экспорт TXT, DOCX
    └── table.py         — экспорт XLSX
```

### Frontend — React + TypeScript + Vite

```
frontend/
├── src/
│   ├── App.tsx          — главный компонент
│   ├── components/
│   │   ├── Uploader.tsx     — drag-and-drop загрузка
│   │   ├── Settings.tsx     — выбор формата экспорта
│   │   ├── ResultPreview.tsx — превью результата
│   │   └── Download.tsx     — скачивание
│   └── api/
│       └── client.ts      — HTTP клиент (axios)
├── package.json
└── vite.config.ts
```

### Docker

```
docker-compose.yml       — backend + frontend
backend/Dockerfile       — Python + OCR deps
frontend/Dockerfile      — Node.js build + Nginx
```

## Пайплайн обработки

1. **Приём** → определение типа файла (PDF/изображение)
2. **Предобработка** → denoise, deskew, contrast, binarization (OpenCV + Pillow)
3. **Типизация** → текст, таблица, или комбинированный
4. **OCR** →
   - Tesseract 5: основной движок для печатного текста
   - Surya OCR: сложные/нечёткие документы
   - Table Transformer: извлечение табличных данных
5. **Постпроцессинг** → коррекция, объединение результатов
6. **Экспорт** → генерация TXT/DOCX/XLSX

## API

| Endpoint | Method | Описание |
|---|---|---|
| `/api/upload` | POST | Загрузка файла, запуск обработки |
| `/api/status/{job_id}` | GET | Статус обработки |
| `/api/result/{job_id}` | GET | Результат (JSON) |
| `/api/download/{job_id}/{format}` | GET | Скачивание файла |

## Стек

**Backend:** fastapi, uvicorn, pytesseract, surya-ocr, transformers, table-transformer,
Pillow, opencv-python, PyMuPDF, python-docx, openpyxl, python-multipart

**Frontend:** react, typescript, vite, axios, react-dropzone

## Верификация

- Запуск `docker compose up`
- Загрузка тестового PDF с текстом и таблицами
- Проверка качества извлечения текста
- Проверка корректности XLSX экспорта
- Проверка времени обработки (≤30 сек)
