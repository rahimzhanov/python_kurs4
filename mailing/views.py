# mailing/views.py
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


class HomeView(TemplateView):
    template_name = 'index.html'


class ClientListView(LoginRequiredMixin, ListView):
    """
    Список всех клиентов текущего пользователя
    """
    model = Client
    template_name = 'mailing/client_list.html'
    context_object_name = 'clients'
    paginate_by = 10  # Пагинация: 10 клиентов на странице

    def get_queryset(self):
        """Показываем только клиентов текущего пользователя"""
        return Client.objects.filter(owner=self.request.user)


class ClientDetailView(LoginRequiredMixin, DetailView):
    """
    Детальная информация о клиенте
    """
    model = Client
    template_name = 'mailing/client_detail.html'
    context_object_name = 'client'

    def get_queryset(self):
        """Проверяем, что клиент принадлежит текущему пользователю"""
        return Client.objects.filter(owner=self.request.user)


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


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    """
    Редактирование клиента
    """
    model = Client
    form_class = ClientForm
    template_name = 'mailing/client_form.html'

    def get_queryset(self):
        """Проверяем, что клиент принадлежит текущему пользователю"""
        return Client.objects.filter(owner=self.request.user)

    def get_success_url(self):
        messages.success(self.request, 'Клиент успешно обновлен!')
        return reverse('client_detail', kwargs={'pk': self.object.pk})


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    """
    Удаление клиента
    """
    model = Client
    template_name = 'mailing/client_confirm_delete.html'
    success_url = reverse_lazy('client_list')

    def get_queryset(self):
        """Проверяем, что клиент принадлежит текущему пользователю"""
        return Client.objects.filter(owner=self.request.user)

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


class MessageDetailView(LoginRequiredMixin, DetailView):
    """
    Детальная страница сообщения

    DetailView - стандартное представление для одного объекта
    """
    model = Message
    template_name = 'mailing/message_detail.html'
    context_object_name = 'message'

    def get_queryset(self):
        """
        Проверяем, что сообщение принадлежит текущему пользователю

        Если пользователь попытается открыть чужое сообщение по URL,
        Django вернет 404 (Not Found), а не покажет чужое сообщение
        """
        return Message.objects.filter(owner=self.request.user)


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


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    """
    Редактирование сообщения

    UpdateView - стандартное представление для редактирования
    """
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message_form.html'

    def get_queryset(self):
        """
        Проверяем, что сообщение принадлежит текущему пользователю

        Это защита от редактирования чужих сообщений
        """
        return Message.objects.filter(owner=self.request.user)

    def get_success_url(self):
        """
        Куда перенаправить после успешного редактирования

        self.object - это отредактированный объект
        """
        messages.success(self.request, 'Сообщение успешно обновлено!')
        return reverse('message_detail', kwargs={'pk': self.object.pk})


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    """
    Удаление сообщения

    DeleteView - стандартное представление для удаления
    """
    model = Message
    template_name = 'mailing/message_confirm_delete.html'
    success_url = reverse_lazy('message_list')

    def get_queryset(self):
        """
        Проверяем, что сообщение принадлежит текущему пользователю
        """
        return Message.objects.filter(owner=self.request.user)

    def delete(self, request, *args, **kwargs):
        """
        Переопределяем метод удаления, чтобы добавить сообщение об успехе
        """
        messages.success(self.request, 'Сообщение успешно удалено!')
        return super().delete(request, *args, **kwargs)




class MailingListView(LoginRequiredMixin, ListView):
    """
    Список всех рассылок текущего пользователя
    """
    model = Mailing
    template_name = 'mailing/mailing_list.html'
    context_object_name = 'mailings'
    paginate_by = 10

    def get_queryset(self):
        """Показываем только свои рассылки, сортируем по дате создания"""
        return Mailing.objects.filter(owner=self.request.user).order_by('-created_at')


class MailingDetailView(LoginRequiredMixin, DetailView):
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

    def get_queryset(self):
        """Проверяем, что рассылка принадлежит текущему пользователю"""
        return Mailing.objects.filter(owner=self.request.user)

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


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    """
    Редактирование рассылки
    """
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_form.html'

    def get_queryset(self):
        """Проверяем, что рассылка принадлежит текущему пользователю"""
        return Mailing.objects.filter(owner=self.request.user)

    def get_form_kwargs(self):
        """Передаем пользователя в форму"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        messages.success(self.request, 'Рассылка успешно обновлена!')
        return reverse('mailing_detail', kwargs={'pk': self.object.pk})


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    """
    Удаление рассылки
    """
    model = Mailing
    template_name = 'mailing/mailing_confirm_delete.html'
    success_url = reverse_lazy('mailing_list')

    def get_queryset(self):
        """Проверяем, что рассылка принадлежит текущему пользователю"""
        return Mailing.objects.filter(owner=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Рассылка успешно удалена!')
        return super().delete(request, *args, **kwargs)