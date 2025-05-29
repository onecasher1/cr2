from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_page, name='home_page'),
    path('search/', views.search_results_view, name='search_results'),

    # Doctors
    path('doctors/', views.doctor_list_all, name='doctor_list_all'),
    path('doctors/<int:doctor_id>/', views.doctor_detail_view, name='doctor_detail'),
    path('doctors/specialization/<int:spec_id>/', views.doctors_by_specialization_view,
         name='doctors_by_specialization'),

    # Specializations
    path('specializations/', views.specialization_list_all, name='specialization_list_all'),

    # Services
    path('services/', views.service_list_view, name='service_list'),

    # Patients CRUD
    path('patients/', views.patient_list_view, name='patient_list'),
    path('patients/new/', views.patient_create_view, name='patient_create'),
    path('patients/<int:pk>/', views.patient_detail_view, name='patient_detail'),
    path('patients/<int:pk>/edit/', views.patient_update_view, name='patient_update'),
    path('patients/<int:pk>/delete/', views.patient_delete_view, name='patient_delete'),

    # Appointments CRUD (Пример)
    path('appointments/', views.appointment_list_all, name='appointment_list_all'),
    path('appointments/new/', views.appointment_create_view, name='appointment_create'),
    path('appointments/<int:pk>/', views.appointment_detail_view, name='appointment_detail_view'),  # Детальный просмотр
    path('appointments/<int:pk>/edit/', views.appointment_update_view, name='appointment_update'),
    path('appointments/<int:pk>/delete/', views.appointment_delete_view, name='appointment_delete'),

    # Medical Records (Заглушка для URL, если будете реализовывать)
    # path('patients/<int:patient_id>/medical-records/', views.medical_record_list_view, name='medical_record_list'),
]