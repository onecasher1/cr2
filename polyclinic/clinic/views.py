from django.shortcuts import render
from .models import Doctor, Appointment, ScheduleError
from django.db.models import Count
from datetime import date, timedelta

def index(request):
    today = date.today()
    tomorrow = today + timedelta(days=1)

    # 1. Топ-5 врачей по числу приёмов (агрегатная функция COUNT)
    top_doctors = Doctor.objects.annotate(appointment_count=Count('appointment')).order_by('-appointment_count')[:5]

    # 2. Ближайшие приёмы (с фильтрацией по дате)
    upcoming_appointments = Appointment.objects.filter(appointment_date__in=[today, tomorrow]).order_by('appointment_date', 'appointment_time')[:10]

    # 3. Последние ошибки
    recent_errors = ScheduleError.objects.order_by('-detected_date')[:5]

    return render(request, 'index.html', {
        'top_doctors': top_doctors,
        'upcoming_appointments': upcoming_appointments,
        'recent_errors': recent_errors,
    })
def search(request):
    query = request.GET.get('q')
    results = Appointment.objects.filter(diagnosis__icontains=query)
    return render(request, 'search.html', {'query': query, 'results': results})
