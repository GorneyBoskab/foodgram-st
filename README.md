# FoodGram - Рецепты

## О проекте
"Фудграм" - это платформа, где пользователи могут публиковать рецепты, добавлять чужие рецепты в избранное, подписываться на публикации других авторов и формировать список покупок для выбранных блюд.

## Технологии
- Python 3.10
- Django 4.2
- Django REST framework
- PostgreSQL
- Docker
- Nginx
- GitHub Actions

## Запуск проекта

### Требования
- Docker
- Docker Compose

### Запуск проекта локально

1. Клонировать репозиторий:
```
git clone https://github.com/yourusername/foodgram-project.git
cd foodgram-project
```

2. Создать файл `.env` в директории `infra` со следующими данными:
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your-very-secret-key-replace-me-in-production
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=adminpassword
```

3. Запустить контейнеры:
```
cd infra
docker-compose up -d
```

По адресу http://localhost изучите фронтенд веб-приложения, а по адресу http://localhost/api/docs/ — спецификацию API.

## API проекта

Документация API доступна по адресу:
```
http://localhost/api/docs/
```

## База данных

Проект использует PostgreSQL. Схема базы данных включает следующие основные модели:
- User - пользователи
- Recipe - рецепты
- Tag - теги для рецептов
- Ingredient - ингредиенты
- RecipeIngredient - связь между рецептами и ингредиентами
- Follow - подписки на авторов
- Favorite - избранные рецепты
- ShoppingCart - список покупок

## Функциональность

- Регистрация и авторизация пользователей (JWT)
- Создание, просмотр, редактирование и удаление рецептов
- Фильтрация рецептов по тегам
- Добавление рецептов в избранное
- Подписка на авторов
- Формирование списка покупок
- Скачивание списка покупок в формате TXT
- Админ-панель для управления контентом

## CI/CD

Настроен автоматический деплой на сервер при пуше в основную ветку через GitHub Actions.

