# mailing/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Client
from .models import Message
from .models import Mailing
from django.utils import timezone


class ClientForm(forms.ModelForm):
    """
    Форма для создания и редактирования клиента
    """

    class Meta:
        model = Client
        fields = ['email', 'full_name', 'comment']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите email получателя'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите Ф.И.О.'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Дополнительная информация (необязательно)',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        """Конструктор - добавляет общие атрибуты"""
        super().__init__(*args, **kwargs)

        # Делаем комментарий необязательным
        self.fields['comment'].required = False

        # Добавляем звездочку для обязательных полей в метках
        self.fields['email'].label = 'Email *'
        self.fields['full_name'].label = 'Ф.И.О. *'

    def clean_email(self):
        """
        Валидация email: проверяем уникальность для текущего пользователя
        """
        email = self.cleaned_data['email']

        # Если это редактирование (уже есть объект)
        if self.instance and self.instance.pk:
            # Проверяем, есть ли другой клиент с таким же email у того же владельца
            if Client.objects.filter(
                    email=email,
                    owner=self.instance.owner
            ).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Клиент с таким email уже существует')
        return email


class MessageForm(forms.ModelForm):
    """
    Форма для создания и редактирования сообщений

    ModelForm - автоматически создает форму на основе модели Message
    """

    class Meta:
        model = Message
        fields = ['subject', 'body']  # Какие поля показывать
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите тему письма'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Введите текст письма',
                'rows': 10
            }),
        }

    def __init__(self, *args, **kwargs):
        """
        Конструктор формы - вызывается при создании объекта формы
        Здесь мы настраиваем внешний вид полей
        """
        super().__init__(*args, **kwargs)

        # Делаем поля обязательными (на всякий случай)
        self.fields['subject'].required = True
        self.fields['body'].required = True

        # Добавляем звездочки для обязательных полей
        self.fields['subject'].label = 'Тема *'
        self.fields['body'].label = 'Текст письма *'

        # Добавляем подсказки
        self.fields['subject'].help_text = 'Кратко опишите, о чем письмо'
        self.fields['body'].help_text = 'Основной текст письма'


class MailingForm(forms.ModelForm):
    """
    Форма для создания и редактирования рассылки

    Особенности:
    1. Поле recipients - множественный выбор клиентов
    2. Валидация дат (start_time < end_time, не в прошлом)
    """

    class Meta:
        model = Mailing
        fields = ['name', 'message', 'recipients', 'start_time', 'end_time', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Новогодняя распродажа'
            }),
            'message': forms.Select(attrs={
                'class': 'form-control'
            }),
            'recipients': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': 10  # Высота списка в строках
            }),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',  # HTML5 виджет для выбора даты
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        """
        Конструктор формы - настраиваем поля под текущего пользователя

        Важно! Мы получаем user через kwargs из view
        """
        self.user = kwargs.pop('user', None)  # Извлекаем пользователя
        super().__init__(*args, **kwargs)

        # Фильтруем сообщения: показываем только сообщения текущего пользователя
        if self.user:
            self.fields['message'].queryset = Message.objects.filter(owner=self.user)

            # Фильтруем клиентов: показываем только клиентов текущего пользователя
            self.fields['recipients'].queryset = Client.objects.filter(owner=self.user)

        # Настройка меток и подсказок
        self.fields['name'].label = 'Название рассылки *'
        self.fields['message'].label = 'Сообщение *'
        self.fields['recipients'].label = 'Получатели *'
        self.fields['start_time'].label = 'Дата и время начала *'
        self.fields['end_time'].label = 'Дата и время окончания *'
        self.fields['is_active'].label = 'Активна (можно отправлять)'

        self.fields['name'].help_text = 'Дайте рассылке понятное название'
        self.fields['message'].help_text = 'Выберите сообщение для отправки'
        self.fields['recipients'].help_text = 'Выберите получателей (можно несколько)'
        self.fields['start_time'].help_text = 'Время, с которого можно начинать отправку'
        self.fields['end_time'].help_text = 'Время, до которого можно отправлять'

    def clean(self):
        """
        Валидация всей формы целиком

        Проверяем:
        1. start_time < end_time
        2. start_time не в прошлом
        """
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            # Проверка 1: дата начала должна быть раньше даты окончания
            if start_time >= end_time:
                raise ValidationError('Дата начала должна быть раньше даты окончания')

            # Проверка 2: дата начала не может быть в прошлом (только для новых рассылок)
            if not self.instance.pk and start_time < timezone.now():
                raise ValidationError('Дата начала не может быть в прошлом')

        return cleaned_data