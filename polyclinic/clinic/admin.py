from django.contrib import admin
from .models import Patient, Doctor, Appointment, ScheduleError
from .forms import AppointmentForm

# INLINE для отображения при просмотре доктора или пациента
class AppointmentInline(admin.TabularInline):
    model = Appointment
    extra = 0
    readonly_fields = ['appointment_date', 'appointment_time', 'duration']
    show_change_link = True


# =========================
# Пациенты
# =========================
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'middle_name', 'gender', 'category', 'age', 'phone')
    list_display_links = ('last_name', 'first_name')
    list_filter = ('gender', 'category', 'registration_date')
    search_fields = ('last_name', 'first_name', 'middle_name', 'phone', 'address')
    date_hierarchy = 'registration_date'
    readonly_fields = ('registration_date',)
    inlines = [AppointmentInline]

    @admin.display(description="Возраст")
    def age(self, obj):
        from datetime import date
        if obj.birth_date:
            return date.today().year - obj.birth_date.year
        return "-"


# =========================
# Врачи
# =========================
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'specialization', 'qualification', 'office_number', 'appointments_count')
    list_display_links = ('last_name', 'first_name')
    list_filter = ('specialization', 'qualification')
    search_fields = ('last_name', 'first_name', 'specialization', 'office_number')
    inlines = [AppointmentInline]

    @admin.display(description="Кол-во приёмов")
    def appointments_count(self, obj):
        return obj.appointment_set.count()


# =========================
# Приёмы
# =========================
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('appointment_date', 'appointment_time', 'doctor', 'patient', 'status')
    list_display_links = ('appointment_date', 'appointment_time')
    list_filter = ('appointment_date', 'status', 'doctor')
    date_hierarchy = 'appointment_date'
    search_fields = (
        'doctor__last_name', 'patient__last_name',
        'diagnosis', 'prescription',
    )
    raw_id_fields = ('doctor', 'patient')
    readonly_fields = ('appointment_date', 'appointment_time')


# =========================
# Ошибки расписания
# =========================
@admin.register(ScheduleError)
class ScheduleErrorAdmin(admin.ModelAdmin):
    list_display = ('error_date', 'error_time', 'doctor', 'short_description_text', 'detected_date')
    list_filter = ('error_date', 'doctor')
    date_hierarchy = 'error_date'
    search_fields = ('doctor__last_name', 'error_description')
    raw_id_fields = ('doctor',)
    readonly_fields = ('detected_date',)
    fields = (
    'patient', 'doctor', 'appointment_date', 'appointment_time', 'duration', 'diagnosis', 'prescription', 'status')
    @admin.display(description="Описание (сокр.)")
    def short_description_text(self, obj):
        return (obj.error_description[:50] + "...") if obj.error_description else "-"
