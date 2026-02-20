# Руководство администратора

## Развертывание системы

### Требования
- Docker и Docker Compose
- PostgreSQL 12+ (или использование контейнера Docker)
- Python 3.8+ (если запуск локально)
- Минимум 1GB RAM для приложения
- Минимум 5GB дискпространства для файлов

### Быстрый старт с Docker

```bash
# 1. Клонируйте репозиторий
git clone <repository-url>
cd electronic_diary

# 2. Создайте .env файл
cp .env.example .env

# 3. Отредактируйте переменные окружения
nano .env

# 4. Запустите контейнеры
docker-compose up -d --build

# 5. Инициализируйте базу данных
docker-compose exec web python init_db.py

# 6. Осуществите доступ к приложению
# Откройте http://localhost:5000 в браузере
```

### Переменные окружения

```
# .env
DATABASE_URL=postgresql://user:password@db:5432/electronic_diary
FLASK_ENV=production
FLASK_SECRET_KEY=your-secret-key-here
MAX_CONTENT_LENGTH=52428800  # 50MB для загрузки файлов
```

## Первоначальная настройка

### 1. Создание первого администратора

```bash
# Подключитесь к контейнеру приложения
docker-compose exec web bash

# Запустите интерактивный скрипт инициализации
python init_db.py
```

### 2. Создание организаций/учреждений

Администратор может создать несколько программ (организаций) без ограничений:

```
Администратор (role='organizer')
├── Математический факультет
│   ├── Алгебра 101
│   ├── Геометрия 201
│   └── Анализ 301
├── Факультет компьютерных наук
│   ├── Python для начинающих
│   ├── Веб-разработка
│   └── Базы данных
```

### 3. Управление пользователями

**Добавление пользователей через интерфейс:**
1. Новые пользователи регистрируются самостоятельно
2. Администратор одобряет и назначает роли при необходимости
3. Организаторы могут добавлять участников в свои программы

**Добавление в программу:**
1. Перейдите к программе
2. Нажмите "Добавить участника"
3. Выберите из списка зарегистрированных пользователей

## Управление хранилищем файлов

### Структура директорий

```
electronic_diary/
├── static/
│   ├── css/
│   ├── uploads/
│   │   └── assignments/          # Загрузки заданий
│   │       └── YYYYMMDD_HHMMSS_* # Файлы участников
```

### Резервное копирование

```bash
# Резервное копирование файлов
docker-compose exec web tar -czf /tmp/uploads_backup.tar.gz /app/static/uploads/

# Резервное копирование базы данных
docker-compose exec db pg_dump -U user electronic_diary > backup.sql

# Полное резервное копирование
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz \
  -C /home/dima/Source electronic_diary/ \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='.env'
```

### Очистка старых файлов

```python
# cleanup_old_files.py
import os
import time
from datetime import datetime, timedelta

UPLOADS_DIR = 'static/uploads/assignments'
DAYS_TO_KEEP = 90

now = time.time()
for filename in os.listdir(UPLOADS_DIR):
    filepath = os.path.join(UPLOADS_DIR, filename)
    if os.path.isfile(filepath):
        if os.stat(filepath).st_mtime < now - DAYS_TO_KEEP * 86400:
            os.remove(filepath)
            print(f"Удален: {filename}")
```

## Мониторинг

### Логи приложения

```bash
# Просмотр логов в реальном времени
docker-compose logs -f web

# Просмотр последних 100 строк логов
docker-compose logs --tail=100 web

# Логи базы данных
docker-compose logs -f db
```

### Производительность

```bash
# Проверка использования ресурсов
docker stats

# Проверка размера контейнеров
docker-compose ps -s
```

## Обслуживание

### Обновление приложения

```bash
# 1. Остановите приложение
docker-compose down

# 2. Обновите код
git pull origin main

# 3. Пересоберите контейнеры
docker-compose up -d --build

# 4. Запустите миграции (если необходимо)
docker-compose exec web python init_db.py
```

### Очистка системы

```bash
# Удаление неиспользуемых контейнеров
docker container prune

# Удаление неиспользуемых томов
docker volume prune

# Полная очистка
docker system prune -a --volumes
```

## Безопасность

### Важные требования

- ✅ Всегда используйте HTTPS в production
- ✅ Устанавливайте сложный пароль администратора
- ✅ Регулярно делайте резервные копии
- ✅ Обновляйте зависимости Python
- ✅ Ограничивайте доступ по IP при возможности

### Настройка SSL/TLS

```bash
# Используйте Nginx или Apache в качестве reverse proxy
# Пример конфигурации nginx:

upstream flask_app {
    server web:5000;
}

server {
    listen 443 ssl http2;
    server_name example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://flask_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Решение проблем

### Приложение не запускается

```bash
# 1. Проверьте переменные окружения
cat .env

# 2. Проверьте логи
docker-compose logs web

# 3. Переинициализируйте БД
docker-compose exec web python init_db.py

# 4. Пересоберите контейнеры
docker-compose up -d --build
```

### Проблемы с загрузкой файлов

```bash
# 1. Проверьте права доступа
ls -la static/uploads/

# 2. Убедитесь, что директория существует
mkdir -p static/uploads/assignments

# 3. Установите права доступа
chmod 755 static/uploads/assignments
```

### Проблемы с подключением к БД

```bash
# 1. Проверьте переменные окружения
echo $DATABASE_URL

# 2. Проверьте работает ли контейнер БД
docker-compose ps db

# 3. Протестируйте подключение
docker-compose exec web psql $DATABASE_URL -c "SELECT 1"
```

## Поддержка и контакты

Для вопросов и проблем:
- Откройте issue на GitHub
- Свяжитесь с администратором системы
- Консультируйтесь с документацией UNIVERSALITY.md

## Версионирование

Текущая версия: **1.0.0**

### Журнал версий

**v1.0.0** (Текущая)
- Универсальная архитектура организатор/участник
- Система управления программами и задачами
- Загрузка и управление файлами
- Система оценок и обратной связи
- Multi-role поддержка
