from django.db import models
from django.utils import timezone
from datetime import time
from django.core.exceptions import ValidationError

class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Мужской'),
        ('F', 'Женский'),
    ]

    CATEGORY_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
    ]

    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    birth_date = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    registration_date = models.DateField()
    category = models.CharField(max_length=3, choices=CATEGORY_CHOICES)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class Doctor(models.Model):
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    specialization = models.CharField(max_length=100)
    qualification = models.CharField(max_length=100)
    office_number = models.CharField(max_length=20)

    def __str__(self):
        return f"Dr. {self.last_name} ({self.specialization})"


class Appointment(models.Model):
    TIME_CHOICES = [
        (time(hour, 0), f"{hour:02d}:00") for hour in range(9, 18)
    ]

    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE)
    appointment_date = models.DateField(default=lambda: timezone.now().date())  # ✅ исправлено
    appointment_time = models.TimeField(choices=TIME_CHOICES)
    duration = models.IntegerField(default=30)
    diagnosis = models.TextField(blank=True)
    prescription = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('запланирован', 'Запланирован'),
        ('завершен', 'Завершён'),
        ('отменён', 'Отменён')
    ], default='запланирован')

    def clean(self):
        super().clean()
        allowed_times = [t[0] for t in self.TIME_CHOICES]
        if self.appointment_time not in allowed_times:
            raise ValidationError("Выберите время приёма с 09:00 до 17:00 (целый час).")

    def __str__(self):
        return f"{self.patient} — {self.appointment_date} {self.appointment_time}"
class ScheduleError(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    error_date = models.DateField()
    error_time = models.TimeField()
    error_description = models.TextField()
    detected_date = models.DateTimeField()

    def __str__(self):
        return f"Error on {self.error_date} ({self.doctor})"
