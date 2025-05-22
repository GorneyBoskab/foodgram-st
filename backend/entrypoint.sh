#!/bin/bash

python manage.py migrate
python manage.py collectstatic --no-input

# Import ingredients data if it doesn't exist
echo "Checking if ingredients need to be imported..."
INGREDIENT_COUNT=$(python manage.py shell -c "from recipes.models import Ingredient; print(Ingredient.objects.count())")
if [ "$INGREDIENT_COUNT" -eq "0" ]; then
    echo "Importing ingredients from data file..."
    if [ -f "/app/data/ingredients.json" ]; then
        python manage.py import_ingredients /app/data/ingredients.json --file_format=json
    elif [ -f "/app/data/ingredients.csv" ]; then
        python manage.py import_ingredients /app/data/ingredients.csv --file_format=csv
    else
        echo "Warning: No ingredient data files found!"
    fi
fi

# Create superuser if specified in environment
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]
then
    python manage.py createsuperuser --noinput
fi

# Start Gunicorn
exec gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000
