# mailing/views.py
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import Client, Message, Mailing, Attempt
from .forms import ClientForm
from django.views.generic import TemplateView
from .models import Message
from .forms import MessageForm
from .forms import MailingForm
from .services import send_mailing
from common.mixins import ManagerOrOwnerMixin


# mailing/views.py

class HomeView(TemplateView):
    """
    Главная страница со статистикой
    """
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Для авторизованных пользователей
        if self.request.user.is_authenticated:
            # Проверяем, является ли пользователь менеджером
            is_manager = self.request.user.groups.filter(name='Managers').exists()

            if is_manager:
                # Менеджер видит ОБЩУЮ статистику по всем пользователям
                context['total_mailings'] = Mailing.objects.count()
                context['total_clients'] = Client.objects.count()
                context['total_messages'] = Message.objects.count()

                # Для активных рассылок нужно проверить статус у всех
                mailings = Mailing.objects.all()
                active_mailings = 0
                for mailing in mailings:
                    if mailing.get_status() == 'running':
                        active_mailings += 1
                context['active_mailings'] = active_mailings

                # Добавляем пометку, что это общая статистика
                context['stats_type'] = 'общая статистика по всем пользователям'

            else:
                # Обычный пользователь видит только свою статистику
                context['total_mailings'] = Mailing.objects.filter(owner=self.request.user).count()
                context['total_clients'] = Client.objects.filter(owner=self.request.user).count()
                context['total_messages'] = Message.objects.filter(owner=self.request.user).count()

                # Активные рассылки только свои
                mailings = Mailing.objects.filter(owner=self.request.user)
                active_mailings = 0
                for mailing in mailings:
                    if mailing.get_status() == 'running':
                        active_mailings += 1
                context['active_mailings'] = active_mailings

                context['stats_type'] = 'ваша личная статистика'

        else:
            # Для неавторизованных - общая статистика по сайту
            context['total_mailings'] = Mailing.objects.count()
            context['total_clients'] = Client.objects.count()
            context['total_messages'] = Message.objects.count()
            context['active_mailings'] = 0
            context['stats_type'] = 'общая статистика сайта'

        return context


class ClientListView(LoginRequiredMixin, ManagerOrOwnerMixin, ListView):
    """
    Список всех клиентов текущего пользователя
    """
    model = Client
    template_name = 'mailing/client_list.html'
    context_object_name = 'clients'
    paginate_by = 10  # Пагинация: 10 клиентов на странице



class ClientDetailView(LoginRequiredMixin, ManagerOrOwnerMixin, DetailView):
    """
    Детальная информация о клиенте
    """
    model = Client
    template_name = 'mailing/client_detail.html'
    context_object_name = 'client'


class ClientCreateView(LoginRequiredMixin, CreateView):
    """
    Создание нового клиента
    """
    model = Client
    form_class = ClientForm
    template_name = 'mailing/client_form.html'
    success_url = reverse_lazy('client_list')

    def form_valid(self, form):
        """
        При создании автоматически устанавливаем владельца
        """
        form.instance.owner = self.request.user
        messages.success(self.request, 'Клиент успешно создан!')
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, ManagerOrOwnerMixin,  UpdateView):
    """
    Редактирование клиента
    """
    model = Client
    form_class = ClientForm
    template_name = 'mailing/client_form.html'

    def get_success_url(self):
        messages.success(self.request, 'Клиент успешно обновлен!')
        return reverse('client_detail', kwargs={'pk': self.object.pk})


class ClientDeleteView(LoginRequiredMixin, ManagerOrOwnerMixin, DeleteView):
    """
    Удаление клиента
    """
    model = Client
    template_name = 'mailing/client_confirm_delete.html'
    success_url = reverse_lazy('client_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Клиент успешно удален!')
        return super().delete(request, *args, **kwargs)


class MessageListView(LoginRequiredMixin, ListView):
    """
    Список всех сообщений текущего пользователя

    LoginRequiredMixin - страница только для авторизованных
    ListView - стандартное представление для списка объектов
    """
    model = Message
    template_name = 'mailing/message_list.html'
    context_object_name = 'messages'  # Имя переменной в шаблоне
    paginate_by = 10  # Пагинация: 10 сообщений на странице

    def get_queryset(self):
        """
        Переопределяем метод получения списка объектов

        Зачем: чтобы показывать только сообщения текущего пользователя
        """
        # Message.objects.all() - вернул бы все сообщения всех пользователей
        # А мы фильтруем по owner = текущий пользователь
        return Message.objects.filter(owner=self.request.user).order_by('-created_at')


class MessageDetailView(LoginRequiredMixin, ManagerOrOwnerMixin, DetailView):
    """
    Детальная страница сообщения

    DetailView - стандартное представление для одного объекта
    """
    model = Message
    template_name = 'mailing/message_detail.html'
    context_object_name = 'message'


class MessageCreateView(LoginRequiredMixin, CreateView):
    """
    Создание нового сообщения

    CreateView - стандартное представление для создания объектов
    """
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('message_list')  # Куда после успешного создания

    def form_valid(self, form):
        """
        Вызывается, когда форма заполнена правильно

        Здесь мы:
        1. Устанавливаем владельца сообщения
        2. Показываем сообщение об успехе
        3. Сохраняем сообщение
        """
        # form.instance - это объект Message, который еще не сохранен в БД
        # Устанавливаем его владельцем текущего пользователя
        form.instance.owner = self.request.user

        # Добавляем flash-сообщение об успехе
        messages.success(self.request, 'Сообщение успешно создано!')

        # Вызываем родительский метод, который сохранит объект
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, ManagerOrOwnerMixin, UpdateView):
    """
    Редактирование сообщения

    UpdateView - стандартное представление для редактирования
    """
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message_form.html'

    def get_success_url(self):
        """
        Куда перенаправить после успешного редактирования

        self.object - это отредактированный объект
        """
        messages.success(self.request, 'Сообщение успешно обновлено!')
        return reverse('message_detail', kwargs={'pk': self.object.pk})


class MessageDeleteView(LoginRequiredMixin, ManagerOrOwnerMixin, DeleteView):
    """
    Удаление сообщения

    DeleteView - стандартное представление для удаления
    """
    model = Message
    template_name = 'mailing/message_confirm_delete.html'
    success_url = reverse_lazy('message_list')

    def delete(self, request, *args, **kwargs):
        """
        Переопределяем метод удаления, чтобы добавить сообщение об успехе
        """
        messages.success(self.request, 'Сообщение успешно удалено!')
        return super().delete(request, *args, **kwargs)


class MailingListView(LoginRequiredMixin,ManagerOrOwnerMixin,  ListView):
    """
    Список всех рассылок текущего пользователя
    """
    model = Mailing
    template_name = 'mailing/mailing_list.html'
    context_object_name = 'mailings'
    paginate_by = 10


class MailingDetailView(LoginRequiredMixin, ManagerOrOwnerMixin, DetailView):
    """
    Детальная страница рассылки
    Здесь будет видно:
    - Основную информацию
    - Статус
    - Статистику отправок
    """
    model = Mailing
    template_name = 'mailing/mailing_detail.html'
    context_object_name = 'mailing'

    def get_context_data(self, **kwargs):
        """
        Добавляем в контекст дополнительную информацию:
        - Статус рассылки
        - Статистику по попыткам отправки
        """
        context = super().get_context_data(**kwargs)
        mailing = self.get_object()

        # Получаем статус (вычисляется в модели)
        context['status'] = mailing.get_status()

        # Статистика по попыткам (если есть)
        attempts = mailing.attempts.all()
        context['total_attempts'] = attempts.count()
        context['success_attempts'] = attempts.filter(status='success').count()
        context['failed_attempts'] = attempts.filter(status='failed').count()

        return context


class MailingCreateView(LoginRequiredMixin, CreateView):
    """
    Создание новой рассылки
    """
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing_list')

    def get_form_kwargs(self):
        """
        Передаем пользователя в форму для фильтрации сообщений и клиентов

        Без этого форма не узнает, какие сообщения и клиенты принадлежат пользователю
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """
        При создании автоматически устанавливаем владельца
        """
        form.instance.owner = self.request.user
        messages.success(self.request, 'Рассылка успешно создана!')
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, ManagerOrOwnerMixin, UpdateView):
    """
    Редактирование рассылки
    """
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_form.html'

    def get_form_kwargs(self):
        """Передаем пользователя в форму"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        messages.success(self.request, 'Рассылка успешно обновлена!')
        return reverse('mailing_detail', kwargs={'pk': self.object.pk})


class MailingDeleteView(LoginRequiredMixin, ManagerOrOwnerMixin, DeleteView):
    """
    Удаление рассылки
    """
    model = Mailing
    template_name = 'mailing/mailing_confirm_delete.html'
    success_url = reverse_lazy('mailing_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Рассылка успешно удалена!')
        return super().delete(request, *args, **kwargs)


class MailingSendView(LoginRequiredMixin, View):
    """
    Представление для запуска рассылки
    Используем View, а не TemplateView, потому что:
    1. Не нужно показывать шаблон
    2. Просто перенаправляем обратно после отправки
    """

    def post(self, request, pk):
        """
        Обрабатываем POST-запрос (кнопка "Запустить")

        POST используется вместо GET для безопасности:
        - Нельзя запустить рассылку просто перейдя по ссылке
        - Требуется подтверждение (кнопка)
        """
        # Получаем рассылку или 404
        mailing = get_object_or_404(Mailing, pk=pk, owner=request.user)

        # Запускаем отправку
        result = send_mailing(mailing)

        # Показываем сообщение пользователю
        if result['success']:
            messages.success(
                request,
                f"✅ Рассылка запущена! {result['message']}"
            )
        else:
            messages.error(
                request,
                f"❌ Ошибка: {result['message']}"
            )

        # Если были ошибки при отправке, показываем детали
        if 'results' in result:
            for item in result['results']:
                if item['status'] == 'failed':
                    messages.warning(
                        request,
                        f"Не удалось отправить {item['email']}: {item.get('error', 'Неизвестная ошибка')}"
                    )

        # Перенаправляем обратно на страницу рассылки
        return redirect('mailing_detail', pk=pk)