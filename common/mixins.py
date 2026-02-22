# common/mixins.py
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.http import Http404


class ManagerRequiredMixin(UserPassesTestMixin):
    """
    Проверка, что пользователь - менеджер
    """

    def test_func(self):
        return self.request.user.groups.filter(name='Менеджеры').exists()

    def handle_no_permission(self):
        messages.error(self.request, 'У вас нет прав для просмотра этой страницы')
        return redirect('home')


    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.groups.filter(name='Менеджеры').exists():
            print(f"Менеджер {self.request.user} видит {queryset.count()} объектов")
            return queryset

        filtered = queryset.filter(owner=self.request.user)
        print(f"Обычный пользователь {self.request.user} видит {filtered.count()} объектов")
        return filtered

class ManagerOrOwnerMixin:
    """
    Миксин для проверки: менеджер или владелец объекта

    - Менеджеры видят ВСЕ объекты
    - Обычные пользователи видят только СВОИ объекты
    """

    def get_queryset(self):
        """
        Получение списка объектов
        """
        queryset = super().get_queryset()

        # Если пользователь - менеджер, показываем ВСЁ
        if self.request.user.groups.filter(name='Managers').exists():
            return queryset  # БЕЗ фильтрации!

        # Если обычный пользователь - только свои объекты
        if hasattr(queryset.model, 'owner'):
            return queryset.filter(owner=self.request.user)

        return queryset

    def get_object(self, queryset=None):
        """
        Получение одного объекта
        """
        obj = super().get_object(queryset)

        # Если пользователь - менеджер, разрешаем любой объект
        if self.request.user.groups.filter(name='Managers').exists():
            return obj

        # Если объект не принадлежит пользователю - 404
        if hasattr(obj, 'owner') and obj.owner != self.request.user:
            raise Http404("Объект не найден")

        return obj


    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.groups.filter(name='Managers').exists():
            print(f"Менеджер {self.request.user} видит {queryset.count()} объектов")
            return queryset

        filtered = queryset.filter(owner=self.request.user)
        print(f"Обычный пользователь {self.request.user} видит {filtered.count()} объектов")
        return filtered