from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Q, Count
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import Http404  # Для get_object_or_404, если нужно обрабатывать исключение вручную

from .models import Appointment, Doctor, Specialization, Patient, Service, MedicalRecord
from .forms import PatientForm, PatientSearchForm, AppointmentForm


def home_page(request):
    today = timezone.now().date()
    upcoming_appointments_qs = Appointment.objects.filter(
        appointment_datetime__date__gte=today,
        status='scheduled'
    ).select_related('patient', 'doctor', 'doctor__specialization').order_by('appointment_datetime')[:5]

    doctors_qs = Doctor.objects.filter(is_active=True).select_related('specialization').order_by('?')[:5]

    specializations_with_doctors_count = Specialization.objects.annotate(
        num_doctors=Count('doctors', filter=Q(doctors__is_active=True))
    ).filter(num_doctors__gt=0).order_by('-num_doctors')[:5]

    context = {
        'upcoming_appointments': upcoming_appointments_qs,
        'doctors': doctors_qs,
        'specializations_with_doctors_count': specializations_with_doctors_count,
        'page_title': 'Главная страница поликлиники'
    }
    return render(request, 'clinic_app/home_page.html', context)


def search_results_view(request):
    query = request.GET.get('q', '').strip()
    doctors_results = []
    services_results = []
    # patients_results = [] # Если нужен поиск по пациентам здесь

    if query:
        doctors_results = Doctor.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(middle_name__icontains=query) |
            Q(specialization__name__icontains=query),
            is_active=True
        ).select_related('specialization').distinct()[:10]

        services_results = Service.objects.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query) |
            Q(description__icontains=query)
        ).prefetch_related('specializations').distinct()[:10]

        # Пример поиска пациентов, если нужно
        # patients_results = Patient.objects.filter(
        #     Q(first_name__icontains=query) |
        #     Q(last_name__icontains=query) |
        #     Q(contact_phone__icontains=query) |
        #     Q(email__icontains=query)
        # ).distinct()[:10]

    context = {
        'query': query,
        'doctors_results': doctors_results,
        'services_results': services_results,
        # 'patients_results': patients_results,
        'page_title': f"Результаты поиска: {query}" if query else "Поиск"
    }
    return render(request, 'clinic_app/search_results.html', context)


# --- Views for Doctors, Specializations, Services (Lists and Details) ---
def doctor_list_all(request):
    doctors_list = Doctor.objects.filter(is_active=True).select_related('specialization').order_by('last_name',
                                                                                                   'first_name')

    # Получаем все специализации, у которых есть активные врачи
    specializations = Specialization.objects.annotate(
        num_doctors=Count('doctors', filter=Q(doctors__is_active=True))
    ).filter(num_doctors__gt=0).order_by('name')

    spec_filter_id_str = request.GET.get('specialization')
    selected_spec_id = None

    if spec_filter_id_str:
        try:
            selected_spec_id = int(spec_filter_id_str)
            doctors_list = doctors_list.filter(specialization__id=selected_spec_id)
        except ValueError:
            selected_spec_id = None  # Игнорируем неверный параметр

    return render(request, 'clinic_app/doctor_list.html', {
        'doctors': doctors_list,
        'specializations': specializations,
        'selected_spec_id': selected_spec_id,
        'page_title': 'Наши врачи'
    })


def doctor_detail_view(request, doctor_id):
    doctor = get_object_or_404(Doctor.objects.select_related('specialization'), pk=doctor_id)

    upcoming_appointments = doctor.appointments.filter(
        appointment_datetime__gte=timezone.now(),
        status='scheduled'
    ).select_related('patient').order_by('appointment_datetime')[:5]

    past_appointments_count = doctor.appointments.filter(
        appointment_datetime__lt=timezone.now(),
        status='completed'
    ).count()

    return render(request, 'clinic_app/doctor_detail.html', {
        'doctor': doctor,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments_count': past_appointments_count,
        'page_title': f"Врач: {doctor.full_name}"
    })


def doctors_by_specialization_view(request, spec_id):
    specialization = get_object_or_404(Specialization, pk=spec_id)
    doctors = Doctor.objects.filter(specialization=specialization, is_active=True).select_related(
        'specialization').order_by('last_name', 'first_name')
    return render(request, 'clinic_app/doctors_by_specialization.html', {
        'specialization': specialization,
        'doctors': doctors,
        'page_title': f"Врачи по специализации: {specialization.name}"
    })


def specialization_list_all(request):
    specializations = Specialization.objects.annotate(
        num_doctors=Count('doctors', filter=Q(doctors__is_active=True))
    ).filter(num_doctors__gt=0).order_by('name')
    return render(request, 'clinic_app/specialization_list.html', {
        'specializations': specializations,
        'page_title': 'Все специализации'
    })


def service_list_view(request):
    services = Service.objects.all().prefetch_related('specializations').order_by('name')
    return render(request, 'clinic_app/service_list.html', {
        'services': services,
        'page_title': 'Наши услуги'
    })


# --- CRUD for Patients ---
def patient_list_view(request):
    search_form = PatientSearchForm(request.GET or None)
    patients = Patient.objects.all().order_by('last_name', 'first_name')

    if search_form.is_valid():
        query = search_form.cleaned_data.get('query', '').strip()
        if query:
            patients = patients.filter(
                Q(last_name__icontains=query) |
                Q(first_name__icontains=query) |
                Q(middle_name__icontains=query) |
                Q(contact_phone__icontains=query) |
                Q(email__icontains=query)
            ).distinct()

    return render(request, 'clinic_app/patient_list.html', {
        'patients': patients,
        'search_form': search_form,
        'page_title': 'Список пациентов'
    })


def patient_detail_view(request, pk):
    patient = get_object_or_404(Patient.objects.prefetch_related(
        'appointments__doctor__specialization',  # Оптимизация для отображения записей
        'medical_records__doctor'  # Оптимизация для отображения мед.карт
    ), pk=pk)

    appointments = patient.appointments.all().order_by('-appointment_datetime')[:10]
    medical_records = patient.medical_records.all().order_by('-record_date')[:10]

    return render(request, 'clinic_app/patient_detail.html', {
        'patient': patient,
        'appointments': appointments,
        'medical_records': medical_records,
        'page_title': f"Карточка пациента: {patient.full_name}"
    })


def patient_create_view(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save()
            messages.success(request, f"Пациент {patient.full_name} успешно зарегистрирован.")
            return redirect('patient_detail', pk=patient.pk)
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
    else:
        form = PatientForm()
    return render(request, 'clinic_app/patient_form.html', {
        'form': form,
        'page_title': 'Регистрация нового пациента',
        'form_title': 'Форма регистрации пациента',
        'button_text': 'Зарегистрировать'
    })


def patient_update_view(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, f"Данные пациента {patient.full_name} успешно обновлены.")
            return redirect('patient_detail', pk=patient.pk)
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
    else:
        form = PatientForm(instance=patient)
    return render(request, 'clinic_app/patient_form.html', {
        'form': form,
        'patient': patient,  # Для отображения в заголовке или ссылке "Отмена"
        'page_title': f"Редактирование: {patient.full_name}",
        'form_title': f'Редактирование данных пациента: {patient.full_name}',
        'button_text': 'Сохранить изменения'
    })


def patient_delete_view(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        patient_name = patient.full_name
        try:
            patient.delete()
            messages.success(request, f"Пациент {patient_name} успешно удален.")
            return redirect('patient_list')
        except models.ProtectedError as e:  # Ловим ProtectedError если есть защищенные связи
            messages.error(request,
                           f"Невозможно удалить пациента {patient_name}, так как с ним связаны другие записи (например, приемы или специализации врачей, если бы Patient был связан с Doctor через PROTECT). Сначала удалите или отвяжите их. Ошибка: {e}")
            return redirect('patient_detail', pk=pk)
    # GET-запрос отобразит страницу подтверждения
    return render(request, 'clinic_app/patient_confirm_delete.html', {
        'patient': patient,
        'page_title': f"Удаление пациента: {patient.full_name}"
    })


# --- CRUD for Appointments ---
def appointment_list_all(request):
    appointments_list = Appointment.objects.all().select_related(
        'patient', 'doctor', 'doctor__specialization'
    ).order_by('-appointment_datetime')

    patient_id_filter_str = request.GET.get('patient_id')
    filtered_patient = None

    if patient_id_filter_str:
        try:
            patient_id_filter_int = int(patient_id_filter_str)
            filtered_patient = get_object_or_404(Patient, pk=patient_id_filter_int)
            appointments_list = appointments_list.filter(patient=filtered_patient)
        except ValueError:
            messages.warning(request, f"Некорректный ID пациента для фильтрации: '{patient_id_filter_str}'.")
        except Http404:  # get_object_or_404 вызовет Http404, если не обрабатывать Patient.DoesNotExist
            messages.warning(request, f"Пациент с ID '{patient_id_filter_str}' не найден. Показаны все записи.")
            filtered_patient = None  # Сбрасываем, так как пациент не найден

    context = {
        'appointments': appointments_list[:50],
        'page_title': 'Все записи на прием',
        'filtered_patient': filtered_patient,
    }
    return render(request, 'clinic_app/appointment_list.html', context)


def appointment_create_view(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            try:
                appointment = form.save()
                messages.success(request,
                                 f"Запись для {appointment.patient.full_name} к врачу {appointment.doctor.full_name} на {appointment.appointment_datetime.strftime('%d.%m.%Y %H:%M')} успешно создана.")
                return redirect('appointment_detail_view', pk=appointment.pk)
            except ValidationError as e:  # Ловим ValidationError из model.clean()
                form.add_error(None, e)  # Добавляем как non_field_error или к конкретному полю, если возможно
                messages.error(request, "Ошибка при создании записи. Проверьте данные.")
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме записи.")
    else:
        form = AppointmentForm()
        # Предзаполнение пациента, если передан ID
        patient_id_str = request.GET.get('patient_id')
        if patient_id_str:
            try:
                patient_id = int(patient_id_str)
                patient = Patient.objects.get(pk=patient_id)
                form.fields['patient'].initial = patient
            except (ValueError, Patient.DoesNotExist):
                messages.warning(request, f"Пациент с ID '{patient_id_str}' для предзаполнения не найден.")

    return render(request, 'clinic_app/appointment_form.html', {
        'form': form,
        'page_title': 'Создать новую запись на прием',
        'form_title': 'Форма записи на прием',
        'button_text': 'Записать'
    })


def appointment_update_view(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            try:
                form.save()
                messages.success(request,
                                 f"Запись на {appointment.appointment_datetime.strftime('%d.%m.%Y %H:%M')} успешно обновлена.")
                return redirect(reverse('appointment_detail_view', kwargs={'pk': appointment.pk}))
            except ValidationError as e:
                form.add_error(None, e)
                messages.error(request, "Ошибка при обновлении записи. Проверьте данные.")
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
    else:
        form = AppointmentForm(instance=appointment)
    return render(request, 'clinic_app/appointment_form.html', {
        'form': form,
        'appointment': appointment,  # Для ссылки "Отмена" и заголовка
        'page_title': f"Редактирование записи на {appointment.appointment_datetime.strftime('%d.%m.%Y %H:%M') if appointment.appointment_datetime else '...'}",
        'form_title': f'Редактирование записи для {appointment.patient.full_name}',
        'button_text': 'Сохранить изменения'
    })


def appointment_delete_view(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        appointment_info = str(appointment)  # Сохраняем информацию до удаления
        appointment.delete()
        messages.success(request, f"Запись {appointment_info} успешно удалена.")
        return redirect('appointment_list_all')
    # GET-запрос отобразит страницу подтверждения
    return render(request, 'clinic_app/appointment_confirm_delete.html', {
        'appointment': appointment,
        'page_title': f"Удаление записи: {str(appointment)}"
    })


def appointment_detail_view(request, pk):
    appointment = get_object_or_404(Appointment.objects.select_related('patient', 'doctor', 'doctor__specialization'),
                                    pk=pk)
    return render(request, 'clinic_app/appointment_detail.html', {
        'appointment': appointment,
        'page_title': f"Детали записи от {appointment.appointment_datetime.strftime('%d.%m.%Y %H:%M') if appointment.appointment_datetime else 'Не указано'}"
    })

# --- Medical Record Views (Заглушки, если будете реализовывать CRUD) ---
# def medical_record_create_for_appointment(request, appointment_pk):
#     appointment = get_object_or_404(Appointment, pk=appointment_pk)
#     # Логика создания мед.записи, связанной с этим приемом
#     # ...
#     return redirect('appointment_detail_view', pk=appointment_pk)

# def medical_record_detail_view(request, pk):
#    record = get_object_or_404(MedicalRecord.objects.select_related('patient', 'doctor', 'appointment'), pk=pk)
#    return render(request, 'clinic_app/medical_record_detail.html', {'record': record})