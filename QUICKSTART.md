# Быстрый старт

## Для пользователей

### 1. Откройте приложение
```
http://localhost
```

### 2. Загрузите документы
- Перетащите файлы в область загрузки
- Или нажмите для выбора файлов
- Поддерживаются: PDF, JPG, PNG, TIFF (до 50MB)

### 3. Выберите форматы экспорта
- TXT — простой текст
- DOCX — документ Word
- XLSX — таблица Excel
- CSV — таблица CSV

### 4. Дождитесь обработки
- Прогресс отображается в реальном времени
- ~30 секунд на страницу

### 5. Скачайте результаты
- Нажмите на кнопку нужного формата
- Файлы сохраняются автоматически

## Для администраторов

### Быстрая установка

```bash
# 1. Клонировать проект
git clone <repo-url> ocr-web-service
cd ocr-web-service

# 2. Загрузить модели OCR
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python ../scripts/download_models.py
deactivate
cd ..

# 3. Запустить сервисы
cd docker
docker-compose up -d

# 4. Проверить
curl http://localhost/api/v1/health
```

### Управление

```bash
# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Перезапуск
docker-compose restart

# Обновление
git pull && docker-compose up -d --build
```

## Решение проблем

### Сервис не запускается
```bash
docker-compose logs backend
docker-compose logs celery-worker
```

### Медленная обработка
- Увеличьте количество Celery workers в docker-compose.yml
- Проверьте загрузку CPU/RAM

### Ошибки памяти
- Увеличьте лимиты памяти для celery-worker
- Рекомендуется минимум 4GB RAM

## Документация

- [Полная инструкция по установке](docs/installation.md)
- [Руководство пользователя](docs/user-guide.md)
- [Руководство по развертыванию](docs/deployment.md)

## Технические характеристики

- **Производительность:** ≤30 сек/страница
- **Точность:** >95% для печатного текста
- **Языки:** Русский (приоритет), латиница
- **Безопасность:** Полная изоляция, без внешних подключений
- **Платформы:** Astra Linux, Windows Server 2019

## Архитектура

```
Nginx (80) → Frontend (React)
           → Backend (FastAPI:8000)
           → Redis (6379)
           → Celery Workers (OCR)
```

## Поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose logs`
2. Проверьте статус: `docker-compose ps`
3. Обратитесь к администратору
