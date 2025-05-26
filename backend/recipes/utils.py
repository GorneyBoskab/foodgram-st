import os
import csv
import json

from django.conf import settings
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.db.models import Model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404


def create_file_from_data(data, file_name, content_type='text/plain'):
    response = HttpResponse(content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    response.write(data)
    return response


def import_json_data(file_path, model_class, field_mapping=None):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'File {file_path} not found')

    field_mapping = field_mapping or {}

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    count = 0
    for item in data:
        if field_mapping:
            for field, value in field_mapping.items():
                if value in item:
                    item[field] = item.pop(value)
        model_class.objects.get_or_create(**item)
        count += 1

    return count


def import_csv_data(file_path, model_class, field_mapping=None):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'File {file_path} not found')

    field_mapping = field_mapping or {}

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            if field_mapping:
                for field, value in field_mapping.items():
                    if value in row:
                        row[field] = row.pop(value)
            model_class.objects.get_or_create(**row)
            count += 1

    return count
