# Скрипт для запуска сервера разработки Django для проекта FoodGram
# Устанавливает виртуальное окружение, активирует его, устанавливает зависимости,
# применяет миграции, импортирует ингредиенты и запускает сервер разработки

# Проверяем, нужно ли очистить проект и начать заново
param(
    [switch]$Clean = $false
)

# Создаем виртуальное окружение, если его нет
if (-not (Test-Path "venv")) {
    Write-Output "Creating virtual environment..."
    python -m venv venv
}

# Активируем виртуальное окружение
Write-Output "Activating virtual environment..."
.\venv\Scripts\Activate

# Устанавливаем зависимости
Write-Output "Installing dependencies..."
pip install -r requirements.txt

# Переходим в каталог backend
cd backend

# Удаляем базу данных и миграции для чистого старта
Remove-Item -Force -Path db.sqlite3 -ErrorAction SilentlyContinue
Get-ChildItem -Path users\migrations\*.py -Exclude "__init__.py" | Remove-Item
Get-ChildItem -Path recipes\migrations\*.py -Exclude "__init__.py" | Remove-Item
Get-ChildItem -Path api\migrations\*.py -Exclude "__init__.py" | Remove-Item

Write-Output "Creating new migrations..."
python manage.py makemigrations users
python manage.py makemigrations recipes
python manage.py makemigrations api

# Применяем миграции
Write-Output "Applying migrations..."
python manage.py migrate

# Проверяем наличие ингредиентов в базе данных и импортируем их, если необходимо
Write-Output "Checking ingredients data..."
$ingredient_count = python -c "import os; import django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodgram.settings'); django.setup(); from recipes.models import Ingredient; print(Ingredient.objects.count())"

if ($ingredient_count -eq "0") {
    Write-Output "Importing ingredients from data files..."
    if (Test-Path "../data/ingredients.json") {
        python manage.py import_ingredients "../data/ingredients.json" --file_format=json
    } elseif (Test-Path "../data/ingredients.csv") {
        python manage.py import_ingredients "../data/ingredients.csv" --file_format=csv
    } else {
        Write-Output "Warning: No ingredient data files found!"
    }
} else {
    Write-Output "Ingredients data already exists in database. Skipping import."
}

# Запускаем сервер разработки
Write-Output "Starting development server..."
python manage.py runserver
