from django.shortcuts import render # Функция для рендеринга HTML-шаблонов
from .models import ABExam        # Импортируем нашу модель

def abexam_list_view(request):
    """
    Представление для отображения списка опубликованных экзаменов.
    """
    # Ваши ФИО и номер группы (замените на реальные)
    fio_student = "Литвинов Георгий Александрович"
    group_number_student = "241-671"

    # Получаем из базы данных все объекты ABExam,
    # у которых поле is_public равно True.
    # .order_by('-exam_date') сортирует результаты по дате экзамена
    # в убывающем порядке (сначала самые свежие).
    published_exams = ABExam.objects.filter(is_public=True).order_by('-exam_date')

    # Контекст - это словарь, который передает данные из view в шаблон.
    # Ключи словаря становятся переменными в шаблоне.
    context = {
        'fio': fio_student,
        'group_number': group_number_student,
        'exams': published_exams, # Список опубликованных экзаменов
        'page_title': 'Список экзаменов (АБ)', # Для тега <title> в HTML
    }

    # render() принимает объект запроса, путь к файлу шаблона и контекст.
    # Она "собирает" HTML-страницу и возвращает ее как HTTP-ответ.
    # Django будет искать шаблон 'main_app/abexam_list.html'
    # внутри папок 'templates' каждого зарегистрированного приложения
    # (если 'APP_DIRS': True в TEMPLATES в settings.py)
    # или в директориях, указанных в 'DIRS' в TEMPLATES.
    return render(request, 'main_app/abexam_list.html', context)