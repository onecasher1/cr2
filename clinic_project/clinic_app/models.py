from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.urls import reverse  # Для get_absolute_url


class Specialization(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name="Название специализации")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Специализация врача"
        verbose_name_plural = "Специализации врачей"
        ordering = ['name']


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name="Аккаунт пользователя (если есть)")
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    middle_name = models.CharField(max_length=100, blank=True, verbose_name="Отчество")
    photo = models.ImageField(upload_to='doctors_photos/', blank=True, null=True, verbose_name="Фото")
    specialization = models.ForeignKey(Specialization, on_delete=models.PROTECT, related_name="doctors",
                                       verbose_name="Специализация")
    experience_years = models.PositiveIntegerField(default=0, verbose_name="Стаж (лет)")
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name="Контактный телефон")
    email = models.EmailField(blank=True, verbose_name="Email")
    room_number = models.CharField(max_length=50, blank=True, verbose_name="Номер кабинета")
    bio = models.TextField(blank=True, verbose_name="Краткая биография/О себе")
    is_active = models.BooleanField(default=True, verbose_name="Активен (работает)")

    def __str__(self):
        return f"Др. {self.last_name} {self.first_name} ({self.specialization.name})"

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name or ''}".strip()

    def get_absolute_url(self):
        return reverse('doctor_detail', kwargs={'doctor_id': self.pk})

    class Meta:
        verbose_name = "Врач"
        verbose_name_plural = "Врачи"
        ordering = ['last_name', 'first_name']


class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name="Аккаунт пользователя (если есть)")
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    middle_name = models.CharField(max_length=100, blank=True, verbose_name="Отчество")
    date_of_birth = models.DateField(verbose_name="Дата рождения")
    address = models.TextField(blank=True, verbose_name="Адрес проживания")
    contact_phone = models.CharField(max_length=20, verbose_name="Контактный телефон")
    email = models.EmailField(unique=True, blank=True, null=True,
                              verbose_name="Email")  # Разрешаем null, если email не обязателен
    insurance_policy_number = models.CharField(max_length=100, blank=True, verbose_name="Номер страхового полиса")
    registration_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
    notes = models.TextField(blank=True, verbose_name="Заметки о пациенте")

    def __str__(self):
        return f"{self.last_name} {self.first_name} (Тел: {self.contact_phone})"

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name or ''}".strip()

    def get_age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                        (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

    get_age.short_description = "Возраст"

    def get_absolute_url(self):
        return reverse('patient_detail', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = "Пациент"
        verbose_name_plural = "Пациенты"
        ordering = ['last_name', 'first_name']


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Запланирован'),
        ('completed', 'Завершен'),
        ('cancelled_by_patient', 'Отменен пациентом'),
        ('cancelled_by_clinic', 'Отменен клиникой'),
        ('no_show', 'Неявка'),
    ]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments", verbose_name="Пациент")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="appointments", verbose_name="Врач")
    appointment_datetime = models.DateTimeField(
        verbose_name="Дата и время приема",
        null=True,  # Разрешаем NULL на уровне базы данных
        blank=True  # Разрешаем быть пустым в формах (важно для пустых инлайнов)
    )
    reason_for_visit = models.CharField(max_length=255, blank=True, verbose_name="Причина визита (кратко)")
    detailed_reason = models.TextField(blank=True, verbose_name="Подробная причина визита/Жалобы")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='scheduled', verbose_name="Статус приема")
    doctor_notes = models.TextField(blank=True, verbose_name="Заметки врача по приему")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания записи")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата последнего изменения")

    def __str__(self):
        # Проверка, чтобы избежать ошибки, если patient или doctor еще не присвоены (например, при создании через пустой инлайн)
        patient_name = self.patient.full_name if self.patient else "Неизвестный пациент"
        doctor_name = self.doctor.full_name if self.doctor else "Неизвестный врач"
        datetime_str = self.appointment_datetime.strftime(
            '%d.%m.%Y %H:%M') if self.appointment_datetime else "Время не указано"

        if self.pk:  # Если объект уже сохранен
            return f"Прием ID {self.pk}: {patient_name} к {doctor_name} в {datetime_str}"
        else:  # Новый, еще не сохраненный объект
            return f"Новая запись: {patient_name} к {doctor_name} ({datetime_str})"

    def clean(self):
        # Вызываем родительский clean в первую очередь
        super().clean()

        # Проводим кастомную валидацию, только если ключевые поля заполнены
        if self.doctor and self.appointment_datetime:
            # Проверка на конфликт времени у врача
            conflicting_appointments = Appointment.objects.filter(
                doctor=self.doctor,
                appointment_datetime__date=self.appointment_datetime.date(),  # Здесь была ошибка
                appointment_datetime__hour=self.appointment_datetime.hour,
                appointment_datetime__minute=self.appointment_datetime.minute,
                status='scheduled'
            ).exclude(pk=self.pk)  # Исключаем текущую запись при редактировании

            if conflicting_appointments.exists():
                raise ValidationError({
                    'appointment_datetime': f"Врач {self.doctor.full_name} уже занят в это время ({self.appointment_datetime.strftime('%d.%m.%Y %H:%M')}). Пожалуйста, выберите другое время."
                })  # Привязываем ошибку к конкретному полю

            # Проверка, что дата приема не в прошлом (для новых записей)
            if not self.pk and self.appointment_datetime < timezone.now():  # self.pk is None для новых объектов
                raise ValidationError({
                    'appointment_datetime': "Нельзя записаться на прием в прошлое время."
                })
        elif not self.pk and not self.appointment_datetime and (
                self.reason_for_visit or self.status != 'scheduled' or self.doctor_notes):
            # Если это новая запись, время не указано, но другие поля заполнены,
            # это означает, что пользователь пытается создать запись без времени.
            # Если appointment_datetime является обязательным для сохранения, форма должна это обработать.
            # Здесь можно добавить дополнительную логику, если нужно.
            # Например, если другие поля заполнены, то appointment_datetime становится обязательным.
            # Однако, если null=True, blank=True, то на уровне модели это разрешено.
            # Валидация обязательности лучше всего делать на уровне формы.
            pass

        # Пример другой сложной бизнес-логики (можно раскомментировать и доработать)
        # if self.patient and self.doctor and self.appointment_datetime and not self.pk:
        #     one_week_ago = self.appointment_datetime.date() - timezone.timedelta(days=7)
        #     one_week_from_appointment = self.appointment_datetime.date() + timezone.timedelta(days=7) # или self.appointment_datetime.date()
        #     appointments_this_week_with_doctor = Appointment.objects.filter(
        #         patient=self.patient,
        #         doctor=self.doctor,
        #         appointment_datetime__date__range=[one_week_ago, one_week_from_appointment],
        #         status='scheduled'
        #     ).count()
        #     MAX_APPOINTMENTS_PER_WEEK = 2
        #     if appointments_this_week_with_doctor >= MAX_APPOINTMENTS_PER_WEEK:
        #         raise ValidationError(
        #             f"Пациент {self.patient.full_name} уже имеет {appointments_this_week_with_doctor} "
        #             f"запланированных(ую) встреч(у) с врачом {self.doctor.full_name} в указанный период. "
        #             f"Максимальное количество: {MAX_APPOINTMENTS_PER_WEEK}."
        #         )

    class Meta:
        verbose_name = "Запись на прием"
        verbose_name_plural = "Записи на прием"
        ordering = ['-appointment_datetime']
        # unique_together больше не требуется, если appointment_datetime может быть NULL,
        # так как уникальность NULL значений обрабатывается по-разному в БД.
        # Если appointment_datetime НЕ ДОЛЖНО БЫТЬ NULL при наличии doctor,
        # то это лучше проверять в clean() или на уровне формы.
        # Либо убрать null=True, blank=True и обрабатывать обязательность на уровне формы инлайна.
        # Для админки с инлайнами, null=True, blank=True часто проще.
        # unique_together = (('doctor', 'appointment_datetime'),) # Если appointment_datetime не может быть NULL


class MedicalRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records',
                                verbose_name="Пациент")
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True,
                                       verbose_name="Связанный прием")
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True,
                               verbose_name="Лечащий врач (создавший запись)")  # blank=True если может быть не указан
    record_date = models.DateField(default=timezone.now, verbose_name="Дата записи")
    diagnosis = models.TextField(blank=True, verbose_name="Диагноз")
    complaints = models.TextField(blank=True, verbose_name="Жалобы")
    examination_data = models.TextField(blank=True, verbose_name="Данные осмотра")
    treatment_plan = models.TextField(blank=True, verbose_name="План лечения")
    recommendations = models.TextField(blank=True, verbose_name="Рекомендации")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания мед. записи")

    def __str__(self):
        patient_name = self.patient.full_name if self.patient else "Неизвестный пациент"
        record_date_str = self.record_date.strftime('%d.%m.%Y') if self.record_date else "Дата не указана"
        return f"Мед. запись для {patient_name} от {record_date_str}"

    class Meta:
        verbose_name = "Медицинская запись"
        verbose_name_plural = "Медицинские записи"
        ordering = ['-record_date', '-created_at']


class Service(models.Model):
    name = models.CharField(max_length=200, verbose_name="Наименование услуги")
    code = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Код услуги")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Стоимость")
    description = models.TextField(blank=True, verbose_name="Описание услуги")
    duration_minutes = models.PositiveIntegerField(blank=True, null=True, verbose_name="Примерная длительность (мин)")
    specializations = models.ManyToManyField(Specialization, blank=True, related_name="services",
                                             verbose_name="Требуемые специализации врачей")

    def __str__(self):
        return f"{self.name} ({self.price} руб.)"

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги клиники"
        ordering = ['name']