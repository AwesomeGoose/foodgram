# Generated by Django 3.2.25 on 2024-12-08 20:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='short_code',
            field=models.CharField(blank=True, max_length=10, null=True, unique=True, verbose_name='Короткий код'),
        ),
    ]
