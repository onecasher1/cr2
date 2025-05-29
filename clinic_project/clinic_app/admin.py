from django.contrib import admin
from django.utils.html import format_html
from django.db import models  # Для models.Count и Q
from django.urls import reverse
from django.utils import timezone
from .models import Specialization, Doctor, Patient, Appointment, MedicalRecord, Service


# --- Инлайн классы ---

class MedicalRecordInline(admin.TabularInline):  # ИЗМЕНЕНИЯ ЗДЕСЬ
    model = MedicalRecord
    fields = ()  # Пусто, если все только для чтения или raw_id.
    # Или ('diagnosis', 'treatment_plan') если хотите их редактировать здесь.

    readonly_fields = ('record_date_display', 'doctor_link_inline', 'diagnosis_short_display',
                       'treatment_plan_short_display', 'created_at_display')
    extra = 0
    show_change_link = True

    @admin.display(description="Диагноз (кратко)")
    def diagnosis_short_display(self, obj):
        if obj.diagnosis and len(obj.diagnosis) > 30:
            return obj.diagnosis[:30] + "..."
        return obj.diagnosis or "-"

    @admin.display(description="Лечение (кратко)")
    def treatment_plan_short_display(self, obj):
        if obj.treatment_plan and len(obj.treatment_plan) > 30:
            return obj.treatment_plan[:30] + "..."
        return obj.treatment_plan or "-"

    @admin.display(description="Врач")
    def doctor_link_inline(self, obj):
        if obj.doctor:
            link = reverse("admin:clinic_app_doctor_change", args=[obj.doctor.id])
            return format_html('<a href="{}">{}</a>', link, obj.doctor.full_name)
        return "-"

    @admin.display(description="Дата записи")
    def record_date_display(self, obj):
        return obj.record_date.strftime('%d.%m.%Y') if obj.record_date else "-"

    @admin.display(description="Создана")
    def created_at_display(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M') if obj.created_at else "-"

    def has_add_permission(self, request, obj=None):
        return False  # Запрет добавления из инлайна

    def has_change_permission(self, request, obj=None):  # Разрешение на переход по ссылке
        return True


class AppointmentInlineForPatient(admin.TabularInline):
    model = Appointment
    fields = ('doctor', 'status')
    readonly_fields = ('appointment_datetime_display', 'created_at_display', 'reason_for_visit_short',
                       'doctor_link_inline_display_for_patient')
    extra = 0
    show_change_link = True
    fk_name = 'patient'
    raw_id_fields = ('doctor',)

    @admin.display(description="Причина (кратко)")
    def reason_for_visit_short(self, obj):
        if obj.reason_for_visit and len(obj.reason_for_visit) > 30:
            return obj.reason_for_visit[:30] + "..."
        return obj.reason_for_visit or "-"

    @admin.display(description="Врач")
    def doctor_link_inline_display_for_patient(self, obj):
        if obj.doctor:
            link = reverse("admin:clinic_app_doctor_change", args=[obj.doctor.id])
            return format_html('<a href="{}">{}</a>', link, obj.doctor.full_name)
        return "-"

    @admin.display(description="Дата и время")
    def appointment_datetime_display(self, obj):
        return obj.appointment_datetime.strftime('%d.%m.%Y %H:%M') if obj.appointment_datetime else "-"

    @admin.display(description="Создана")
    def created_at_display(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M') if obj.created_at else "-"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('doctor', 'doctor__specialization').order_by(
            '-appointment_datetime')


class AppointmentInlineForDoctor(admin.TabularInline):
    model = Appointment
    fields = ('patient', 'status')
    readonly_fields = ('appointment_datetime_display', 'created_at_display', 'reason_for_visit_short',
                       'patient_link_inline_display_for_doctor')
    extra = 0
    show_change_link = True
    fk_name = 'doctor'
    raw_id_fields = ('patient',)

    @admin.display(description="Причина (кратко)")
    def reason_for_visit_short(self, obj):
        if obj.reason_for_visit and len(obj.reason_for_visit) > 30:
            return obj.reason_for_visit[:30] + "..."
        return obj.reason_for_visit or "-"

    @admin.display(description="Пациент")
    def patient_link_inline_display_for_doctor(self, obj):
        if obj.patient:
            link = reverse("admin:clinic_app_patient_change", args=[obj.patient.id])
            return format_html('<a href="{}">{}</a>', link, obj.patient.full_name)
        return "-"

    @admin.display(description="Дата и время")
    def appointment_datetime_display(self, obj):
        return obj.appointment_datetime.strftime('%d.%m.%Y %H:%M') if obj.appointment_datetime else "-"

    @admin.display(description="Создана")
    def created_at_display(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M') if obj.created_at else "-"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('patient').order_by('-appointment_datetime')


# --- Основные Admin классы ---

@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_short', 'doctors_count_display')
    search_fields = ('name',)

    @admin.display(description="Краткое описание")
    def description_short(self, obj):
        if obj.description and len(obj.description) > 50:
            return obj.description[:50] + "..."
        return obj.description or "-"

    @admin.display(description="Кол-во врачей", ordering='doctors_count_annotated')
    def doctors_count_display(self, obj):
        return obj.doctors_count_annotated

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            doctors_count_annotated=models.Count('doctors', filter=models.Q(doctors__is_active=True)))
        return queryset


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
    'full_name_link', 'date_of_birth', 'get_age_display', 'contact_phone', 'email', 'registration_date_formatted',
    'total_appointments_display')
    list_display_links = ('full_name_link',)
    list_filter = ('registration_date', ('date_of_birth', admin.DateFieldListFilter))
    search_fields = ('last_name', 'first_name', 'middle_name', 'contact_phone', 'email', 'insurance_policy_number')
    date_hierarchy = 'registration_date'
    readonly_fields = ('registration_date', 'get_age_display')
    fieldsets = (
        ("Основная информация", {
            'fields': (
            ('last_name', 'first_name', 'middle_name'), 'date_of_birth', 'get_age_display', 'contact_phone', 'email')
        }),
        ("Дополнительная информация", {
            'fields': ('address', 'insurance_policy_number', 'notes'),
            'classes': ('collapse',)
        }),
        ("Системная информация", {
            'fields': ('user', 'registration_date'),
            'classes': ('collapse',)
        }),
    )
    inlines = [AppointmentInlineForPatient, MedicalRecordInline]  # MedicalRecordInline используется здесь
    raw_id_fields = ('user',)

    @admin.display(description="ФИО Пациента", ordering='last_name')
    def full_name_link(self, obj):
        return str(obj.full_name)

    @admin.display(description="Дата регистрации", ordering='registration_date')
    def registration_date_formatted(self, obj):
        return obj.registration_date.strftime('%d.%m.%Y %H:%M')

    @admin.display(description="Возраст")
    def get_age_display(self, obj):
        age = obj.get_age()
        return age if age is not None else "N/A"

    @admin.display(description="Всего записей на прием", ordering='appointments_count_annotated')
    def total_appointments_display(self, obj):
        return obj.appointments_count_annotated

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(appointments_count_annotated=models.Count('appointments'))
        return queryset


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
    'photo_thumbnail', 'full_name_link', 'specialization', 'experience_years', 'contact_phone', 'is_active',
    'upcoming_appointments_count_display')
    list_display_links = ('full_name_link',)
    list_filter = ('specialization', 'is_active', 'experience_years')
    search_fields = ('last_name', 'first_name', 'specialization__name', 'room_number')
    readonly_fields = ('photo_preview',)
    fieldsets = (
        (None, {'fields': ('last_name', 'first_name', 'middle_name')}),
        ('Контактная и профессиональная информация', {
            'fields': (
            'specialization', 'experience_years', 'contact_phone', 'email', 'room_number', 'bio', 'is_active')
        }),
        ('Фотография', {'fields': ('photo', 'photo_preview')}),
        ('Системная информация', {'fields': ('user',), 'classes': ('collapse',)})
    )
    inlines = [AppointmentInlineForDoctor]  # MedicalRecordInline здесь не используется
    raw_id_fields = ('user',)

    @admin.display(description="Фото")
    def photo_thumbnail(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" width="50" height="auto" style="object-fit: cover; border-radius: 5px;" />',
                obj.photo.url)
        return "Нет фото"

    @admin.display(description="Превью фото")
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="200" height="auto" />', obj.photo.url)
        return "Фото не загружено"

    @admin.display(description="ФИО Врача", ordering='last_name')
    def full_name_link(self, obj):
        return str(obj.full_name)

    @admin.display(description="Ближайшие приемы (кол-во)", ordering='upcoming_appointments_count_annotated')
    def upcoming_appointments_count_display(self, obj):
        return obj.upcoming_appointments_count_annotated

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            upcoming_appointments_count_annotated=models.Count(
                'appointments',
                filter=models.Q(appointments__appointment_datetime__gte=timezone.now(),
                                appointments__status='scheduled')
            )
        )
        return queryset


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
    'patient_link', 'doctor_link', 'appointment_datetime_formatted', 'status', 'reason_for_visit_short_display',
    'created_at_formatted')
    list_display_links = None
    list_filter = (
    'status', ('appointment_datetime', admin.DateFieldListFilter), 'doctor__specialization', 'doctor', 'patient')
    search_fields = (
    'patient__last_name', 'patient__first_name', 'doctor__last_name', 'doctor__first_name', 'reason_for_visit')
    date_hierarchy = 'appointment_datetime'
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('patient', 'doctor')
    actions = ['mark_as_completed', 'mark_as_cancelled_by_clinic', 'mark_as_no_show']
    list_select_related = ('patient', 'doctor', 'doctor__specialization')

    fieldsets = (
        ("Основная информация", {
            'fields': ('patient', 'doctor', 'appointment_datetime', 'status')
        }),
        ("Детали визита", {
            'fields': ('reason_for_visit', 'detailed_reason', 'doctor_notes')
        }),
        ("Системная информация", {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    @admin.display(description="Пациент", ordering='patient__last_name')
    def patient_link(self, obj):
        url = reverse('admin:clinic_app_patient_change', args=[obj.patient.pk])
        return format_html('<a href="{}">{}</a>', url, obj.patient.full_name)

    @admin.display(description="Врач", ordering='doctor__last_name')
    def doctor_link(self, obj):
        url = reverse('admin:clinic_app_doctor_change', args=[obj.doctor.pk])
        return format_html('<a href="{}">{}</a>', url, obj.doctor.full_name)

    @admin.display(description="Дата и время приема", ordering='appointment_datetime')
    def appointment_datetime_formatted(self, obj):
        return obj.appointment_datetime.strftime('%d.%m.%Y %H:%M')

    @admin.display(description="Причина (кратко)")
    def reason_for_visit_short_display(self, obj):
        if obj.reason_for_visit and len(obj.reason_for_visit) > 50:
            return obj.reason_for_visit[:50] + "..."
        return obj.reason_for_visit or "-"

    @admin.display(description="Дата создания", ordering='created_at')
    def created_at_formatted(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')

    @admin.action(description="Пометить выбранные как 'Завершен'")
    def mark_as_completed(self, request, queryset):
        updated_count = queryset.update(status='completed')
        self.message_user(request, f"{updated_count} приемов помечены как 'Завершен'.")

    @admin.action(description="Пометить выбранные как 'Отменен клиникой'")
    def mark_as_cancelled_by_clinic(self, request, queryset):
        updated_count = queryset.update(status='cancelled_by_clinic')
        self.message_user(request, f"{updated_count} приемов помечены как 'Отменен клиникой'.")

    @admin.action(description="Пометить выбранные как 'Неявка'")
    def mark_as_no_show(self, request, queryset):
        updated_count = queryset.update(status='no_show')
        self.message_user(request, f"{updated_count} приемов помечены как 'Неявка'.")


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = (
    'patient_link', 'doctor_link', 'record_date_formatted', 'diagnosis_short_display', 'appointment_link')
    list_filter = (('record_date', admin.DateFieldListFilter), 'doctor__specialization', 'doctor', 'patient')
    search_fields = ('patient__last_name', 'patient__first_name', 'doctor__last_name', 'diagnosis', 'treatment_plan')
    date_hierarchy = 'record_date'
    readonly_fields = ('created_at',)
    raw_id_fields = ('patient', 'doctor', 'appointment')
    list_select_related = ('patient', 'doctor', 'appointment', 'doctor__specialization')

    fieldsets = (
        ("Основная информация", {
            'fields': ('patient', 'doctor', 'record_date', 'appointment')
        }),
        ("Медицинские данные", {
            'fields': ('complaints', 'examination_data', 'diagnosis', 'treatment_plan', 'recommendations')
        }),
        ("Системная информация", {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    @admin.display(description="Пациент", ordering='patient__last_name')
    def patient_link(self, obj):
        url = reverse('admin:clinic_app_patient_change', args=[obj.patient.pk])
        return format_html('<a href="{}">{}</a>', url, obj.patient.full_name)

    @admin.display(description="Врач", ordering='doctor__last_name')
    def doctor_link(self, obj):
        if obj.doctor:
            url = reverse('admin:clinic_app_doctor_change', args=[obj.doctor.pk])
            return format_html('<a href="{}">{}</a>', url, obj.doctor.full_name)
        return "N/A"

    @admin.display(description="Дата записи", ordering='record_date')
    def record_date_formatted(self, obj):
        return obj.record_date.strftime('%d.%m.%Y')

    @admin.display(description="Диагноз (кратко)")
    def diagnosis_short_display(self, obj):  # Для list_display основной админки MedicalRecord
        if obj.diagnosis and len(obj.diagnosis) > 50:
            return obj.diagnosis[:50] + "..."
        return obj.diagnosis or "-"

    @admin.display(description="Связанный прием")
    def appointment_link(self, obj):
        if obj.appointment:
            url = reverse('admin:clinic_app_appointment_change', args=[obj.appointment.pk])
            return format_html('<a href="{}">Прием от {}</a>', url,
                               obj.appointment.appointment_datetime.strftime('%d.%m.%Y %H:%M'))
        return "Нет связанного приема"


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'price', 'duration_minutes', 'display_specializations')
    search_fields = ('name', 'code')
    list_filter = ('specializations',)
    filter_horizontal = ('specializations',)

    @admin.display(description="Требуемые специализации")
    def display_specializations(self, obj):
        return ", ".join([spec.name for spec in obj.specializations.all()]) if obj.specializations.exists() else "-"