from django.db import models
from django.contrib.auth.models import User # Стандартная модель пользователя Django
from django.utils import timezone # Для работы с датой и временем, включая часовые пояса

# Замените 'ABExam' на ваше название, например, 'MDExam'
class ABExam(models.Model):
    """
    Модель для хранения информации об экзаменах.
    """

    # Поле для названия экзамена
    # CharField - для текстовых строк ограниченной длины.
    # max_length - обязательный параметр для CharField, максимальная длина строки.
    # verbose_name - человекочитаемое имя поля, будет использоваться в админке и формах.
    exam_name = models.CharField(
        max_length=255,
        verbose_name="Название экзамена"
    )

    # Поле для даты создания записи
    # DateTimeField - для хранения даты и времени.
    # auto_now_add=True - автоматически устанавливает текущую дату и время
    #                     при создании объекта (записи в таблице).
    #                     Это поле становится нередактируемым.
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания записи"
    )

    # Поле для даты проведения экзамена
    # DateField - для хранения только даты (без времени).
    # default=timezone.now - устанавливает текущую дату как значение по умолчанию,
    #                        если при создании объекта значение не предоставлено.
    #                        Пользователь может изменить это значение.
    exam_date = models.DateField(
        verbose_name="Дата проведения экзамена",
        default=timezone.now
    )

    # Поле для изображения (задание по экзамену)
    # ImageField - специальное поле для загрузки изображений.
    #              Требует установки библиотеки Pillow (`pip install Pillow`).
    # upload_to='exam_images/' - указывает подпапку внутри MEDIA_ROOT,
    #                            куда будут сохраняться загруженные изображения.
    #                            Django автоматически создаст эту папку, если ее нет.
    # blank=True - поле может быть пустым в формах Django (необязательно для заполнения).
    # null=True - поле может иметь значение NULL в базе данных.
    #             Для CharField и TextField лучше избегать null=True, но для ImageField это нормально.
    exam_image = models.ImageField(
        upload_to='exam_images/',
        verbose_name="Задание (изображение)",
        blank=True,
        null=True
    )

    # Поле для связи "многие ко многим" с моделью User
    # ManyToManyField - определяет связь "многие ко многим".
    #                   Один экзамен могут писать много пользователей,
    #                   и один пользователь может быть назначен на много экзаменов.
    # User - ссылаемся на стандартную модель пользователя Django.
    # verbose_name - человекочитаемое имя.
    # related_name='assigned_exams' - имя для обратной связи.
    #                                 Позволяет от объекта User получить все экзамены,
    #                                 на которые он назначен: user.assigned_exams.all().
    # blank=True - можно создать экзамен, не назначив сразу пользователей.
    examinees = models.ManyToManyField(
        User,
        verbose_name="Экзаменуемые",
        related_name="assigned_exams",
        blank=True
    )

    # Поле для флага публикации
    # BooleanField - для хранения булевых значений (True/False).
    # default=False - по умолчанию запись не опубликована.
    is_public = models.BooleanField(
        default=False,
        verbose_name="Опубликовано"
    )

    # Метод __str__ определяет строковое представление объекта.
    # Это то, что вы увидите, например, в админке Django или при выводе объекта.
    def __str__(self):
        return f"{self.exam_name} ({self.exam_date.strftime('%d.%m.%Y')})"

    # Класс Meta позволяет задать метаданные для модели.
    class Meta:
        # verbose_name - имя модели в единственном числе для админки.
        verbose_name = "Экзамен (АБ)" # Замените АБ
        # verbose_name_plural - имя модели во множественном числе для админки.
        verbose_name_plural = "Экзамены (АБ)" # Замените АБ
        # ordering - определяет порядок сортировки записей по умолчанию
        #            при извлечении их из базы данных.
        #            '-exam_date' - сортировка по дате экзамена в обратном порядке (сначала новые).
        #            'exam_name' - вторичная сортировка по названию экзамена.
        ordering = ['-exam_date', 'exam_name']