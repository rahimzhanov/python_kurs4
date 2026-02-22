# users/views.py
from django.views import View
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from django.core.mail import send_mail
from django.conf import settings
from .forms import UserRegistrationForm
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from .models import User
from common.mixins import ManagerRequiredMixin


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

    class ManagerRequiredMixin(UserPassesTestMixin):
        """Проверка, что пользователь - менеджер"""

        def test_func(self):
            return self.request.user.groups.filter(name='Менеджеры').exists()

        def handle_no_permission(self):
            messages.error(self.request, 'У вас нет прав для просмотра этой страницы')
            return redirect('home')



class UserListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
        """
        Список пользователей (только для менеджеров)
        """
        model = User
        template_name = 'users/user_list.html'
        context_object_name = 'users'
        paginate_by = 20

        def get_queryset(self):
            return User.objects.all().order_by('-date_joined')

class UserToggleActiveView(LoginRequiredMixin, ManagerRequiredMixin, View):
        """
        Блокировка/разблокировка пользователя (только для менеджеров)
        """

        def post(self, request, pk):
            user = get_object_or_404(User, pk=pk)

            # Не даем заблокировать самого себя
            if user == request.user:
                messages.error(request, 'Нельзя заблокировать самого себя')
                return redirect('user_list')

            # Переключаем статус
            user.is_active = not user.is_active
            user.save()

            status = 'активирован' if user.is_active else 'заблокирован'
            messages.success(request, f'Пользователь {user.email} {status}')

            return redirect('user_list')
