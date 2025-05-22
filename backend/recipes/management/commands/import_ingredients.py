"""Команда импорта ингредиентов."""
import csv
import json
import os

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Импорт ингредиентов из JSON или CSV файла."""

    help = 'Import ingredients from JSON or CSV file'

    def add_arguments(self, parser):
        """Добавление аргументов команды."""
        parser.add_argument(
            'file_path',
            type=str,
            help='Path to the file with ingredients data'
        )
        parser.add_argument(
            '--file_format',
            type=str,
            default='json',
            help='Format of the file with ingredients data (json or csv)'
        )

    def handle(self, *args, **options):
        """Обработчик команды."""
        file_path = options['file_path']
        file_format = options['file_format'].lower()

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(
                f'File {file_path} does not exist'
            ))
            return

        try:
            if file_format == 'json':
                self.import_from_json(file_path)
            elif file_format == 'csv':
                self.import_from_csv(file_path)
            else:
                self.stdout.write(self.style.ERROR(
                    f'Unsupported file format: {file_format}'
                ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))

    def import_from_json(self, file_path):
        """Импорт ингредиентов из JSON файла."""
        with open(file_path, 'r', encoding='utf-8') as f:
            ingredients = json.load(f)

        count = 0
        for item in ingredients:
            name = item.get('name')
            measurement_unit = item.get('measurement_unit')
            if not name or not measurement_unit:
                self.stdout.write(self.style.WARNING(
                    'Skipping ingredient with missing name or measurement_unit'
                ))
                continue

            Ingredient.objects.get_or_create(
                name=name,
                measurement_unit=measurement_unit
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Successfully imported {count} ingredients from JSON'
        ))

    def import_from_csv(self, file_path):
        """Импорт ингредиентов из CSV файла."""
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            count = 0
            for row in reader:
                if len(row) >= 2:
                    name, measurement_unit = row[:2]
                    Ingredient.objects.get_or_create(
                        name=name,
                        measurement_unit=measurement_unit
                    )
                    count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Successfully imported {count} ingredients from CSV'
        ))
