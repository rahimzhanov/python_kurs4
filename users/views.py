# users/views.py
from django.shortcuts import render, redirect
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.core.mail import send_mail
from django.conf import settings
from .forms import UserRegistrationForm
from .models import User


class RegisterView(CreateView):
    """
    Представление для регистрации новых пользователей

    CreateView - стандартное представление Django для создания объектов
    В данном случае мы создаем объект User
    """
    model = User
    form_class = UserRegistrationForm
    template_name = 'users/register.html'  # Шаблон для отображения
    success_url = reverse_lazy('login')  # Куда перенаправить после успешной регистрации

    def form_valid(self, form):
        """
        Вызывается, когда форма заполнена правильно

        Здесь мы добавляем отправку приветственного письма
        """
        # Сначала сохраняем пользователя (вызываем родительский метод)
        response = super().form_valid(form)

        # Получаем только что созданного пользователя
        user = self.object

        # Отправляем приветственное письмо
        try:
            send_mail(
                subject='Добро пожаловать в Сервис рассылок!',
                message=f'Здравствуйте, {user.email}!\n\n'
                        f'Вы успешно зарегистрировались на нашем сайте.\n'
                        f'Теперь вы можете создавать свои рассылки и управлять клиентами.\n\n'
                        f'С уважением,\n'
                        f'Команда Сервиса рассылок',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,  # Если не получится отправить - будет ошибка
            )
        except Exception as e:
            # Логируем ошибку, но не прерываем регистрацию
            print(f"Ошибка отправки письма: {e}")

        return response


class CustomLoginView(LoginView):
    """
    Представление для входа пользователя

    LoginView - стандартное представление Django для авторизации
    """
    template_name = 'users/login.html'  # Шаблон для входа

    def get_success_url(self):
        """
        Куда перенаправить после успешного входа
        """
        return reverse_lazy('home')  # На главную страницу