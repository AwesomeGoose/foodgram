import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from recipes.models import Ingredient, Tag

DATA_FILES = {
    Ingredient: "ingredients.csv",
    Tag: "tags.csv",
}


class Command(BaseCommand):
    help = "Добавляет данные в базу данных из CSV файлов"

    def handle(self, *args, **options):
        base_path = Path(settings.BASE_DIR) / "data"
        for model, filename in DATA_FILES.items():
            file_path = base_path / filename
            if not file_path.exists():
                self.stderr.write(self.style.ERROR(f"Файл {filename} не найден"))
                continue

            try:
                with file_path.open("r", encoding="utf-8") as file:
                    csv_reader = csv.DictReader(file)
                    for row in csv_reader:
                        try:
                            model.objects.update_or_create(**row)
                        except IntegrityError as error:
                            self.stderr.write(
                                self.style.ERROR(
                                    f"Ошибка при добавлении записи в {model.__name__}: {error}"
                                )
                            )
                self.stdout.write(
                    self.style.SUCCESS(f"Данные для {model.__name__} успешно загружены")
                )
            except Exception as error:
                self.stderr.write(
                    self.style.ERROR(f"Произошла ошибка при обработке {filename}: {error}")
                )
