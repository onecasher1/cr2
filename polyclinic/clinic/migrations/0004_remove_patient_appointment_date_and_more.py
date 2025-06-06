# Generated by Django 5.2 on 2025-05-17 16:44

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0003_patient_appointment_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='patient',
            name='appointment_date',
        ),
        migrations.AlterField(
            model_name='appointment',
            name='appointment_date',
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='appointment_time',
            field=models.TimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='diagnosis',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='duration',
            field=models.IntegerField(default=30),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='prescription',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='status',
            field=models.CharField(choices=[('запланирован', 'Запланирован'), ('завершен', 'Завершён'), ('отменён', 'Отменён')], default='запланирован', max_length=20),
        ),
        migrations.AlterField(
            model_name='patient',
            name='registration_date',
            field=models.DateField(),
        ),
    ]
