# mailing/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class Client(models.Model):
    """
    Модель получателя рассылки (клиента)
    """
    email = models.EmailField(
        unique=True,                    # Каждый email должен быть уникальным
        verbose_name='Email',            # Название поля в админке
        help_text='Введите email получателя'  # Подсказка при вводе
    )
    full_name = models.CharField(
        max_length=255,                  # Максимальная длина строки
        verbose_name='Ф.И.О.',
        help_text='Введите полное имя получателя'
    )
    comment = models.TextField(
        verbose_name='Комментарий',
        blank=True,                      # Может быть пустым (не обязательно)
        null=True,                        # В базе данных может быть NULL
        help_text='Дополнительная информация о клиенте'
    )
    owner = models.ForeignKey(
        User,                            # Связь с моделью User
        on_delete=models.CASCADE,         # При удалении пользователя удаляются все его клиенты
        verbose_name='Владелец',
        related_name='clients'            # Обратная связь: user.clients.all()
    )
    created_at = models.DateTimeField(
        auto_now_add=True,                 # Устанавливается только при создании
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,                     # Обновляется при каждом сохранении
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Клиент'            # Название в единственном числе
        verbose_name_plural = 'Клиенты'    # Название во множественном числе
        ordering = ['full_name', 'email']  # Сортировка по умолчанию

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class Message(models.Model):
    """
    Модель сообщения для рассылки
    """
    subject = models.CharField(
        max_length=255,
        verbose_name='Тема письма',
        help_text='Введите тему сообщения'
    )
    body = models.TextField(
        verbose_name='Тело письма',
        help_text='Введите текст сообщения'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Владелец',
        related_name='messages'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} ({self.created_at.strftime('%d.%m.%Y')})"


class Mailing(models.Model):
    """
    Модель рассылки
    """

    # Вложенный класс для выбора статуса
    class Status(models.TextChoices):
        CREATED = 'created', 'Создана'  # (значение в БД, отображение)
        RUNNING = 'running', 'Запущена'
        COMPLETED = 'completed', 'Завершена'

    name = models.CharField(
        max_length=255,
        verbose_name='Название рассылки',
        help_text='Введите название рассылки'
    )
    start_time = models.DateTimeField(
        verbose_name='Дата и время начала',
        help_text='Укажите дату и время начала рассылки'
    )
    end_time = models.DateTimeField(
        verbose_name='Дата и время окончания',
        help_text='Укажите дату и время окончания рассылки'
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,  # Если удалено сообщение - удалить рассылку
        verbose_name='Сообщение',
        related_name='mailings'  # message.mailings.all()
    )
    recipients = models.ManyToManyField(
        Client,
        verbose_name='Получатели',
        related_name='mailings'  # client.mailings.all() (обратная связь)
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Владелец',
        related_name='mailings'  # user.mailings.all()
    )
    is_active = models.BooleanField(
        default=True,  # По умолчанию активна
        verbose_name='Активна',
        help_text='Отметьте, если рассылка активна'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
        ordering = ['-created_at']
        permissions = [  # Кастомные права доступа
            ('can_view_all_mailings', 'Может просматривать все рассылки'),
            ('can_disable_mailing', 'Может отключать рассылки'),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def get_status(self):
        """
        Вычисляет текущий статус рассылки на основе дат
        """
        now = timezone.now()  # Текущее время с учетом часового пояса

        if now < self.start_time:
            return self.Status.CREATED  # Еще не началась
        elif self.start_time <= now <= self.end_time:
            return self.Status.RUNNING  # Идет прямо сейчас
        else:
            return self.Status.COMPLETED  # Уже закончилась

    get_status.short_description = 'Статус'  # Название колонки в админке

    @property
    def status(self):
        """
        Свойство для удобного доступа: mailing.status вместо mailing.get_status()
        """
        return self.get_status()

    def clean(self):
        """
        Валидация дат (вызывается автоматически при сохранении через формы)
        """
        from django.core.exceptions import ValidationError

        if self.start_time and self.end_time:
            # Проверка 1: дата начала должна быть раньше даты окончания
            if self.start_time >= self.end_time:
                raise ValidationError('Дата начала должна быть раньше даты окончания')

            # Проверка 2: дата начала не может быть в прошлом
            if self.start_time < timezone.now():
                raise ValidationError('Дата начала не может быть в прошлом')


class Attempt(models.Model):
    """
    Модель попытки отправки рассылки
    """
    class Status(models.TextChoices):
        SUCCESS = 'success', 'Успешно'
        FAILED = 'failed', 'Не успешно'

    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        verbose_name='Рассылка',
        related_name='attempts'              # mailing.attempts.all()
    )
    attempt_time = models.DateTimeField(
        auto_now_add=True,                    # Автоматически при создании записи
        verbose_name='Дата и время попытки'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,                # Выбор из Status
        verbose_name='Статус'
    )
    server_response = models.TextField(
        verbose_name='Ответ сервера',
        blank=True,                            # Может быть пустым
        null=True                              # В БД может быть NULL
    )
    recipient_email = models.EmailField(
        verbose_name='Email получателя',
        help_text='Email, на который отправлялось письмо'
    )
    error_message = models.TextField(
        verbose_name='Сообщение об ошибке',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Попытка отправки'
        verbose_name_plural = 'Попытки отправки'
        ordering = ['-attempt_time']            # Сначала свежие

    def __str__(self):
        return f"{self.mailing.name} - {self.recipient_email} - {self.get_status_display()}"