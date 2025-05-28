# main_app/urls.py
from django.urls import path
from . import views # Импортируем views из текущего приложения

# app_name полезен для именования URL-ов и использования их в шаблонах
# через {% url 'main_app:abexam_list_page' %}
app_name = 'main_app'

urlpatterns = [
    # path('имя_url_в_браузере/', views.имя_функции_во_views, name='имя_для_ссылок_в_коде')
    # Замените 'abexam' на ваше название URL, например 'mdexam'
    path('abexam/', views.abexam_list_view, name='abexam_list_page'),
]