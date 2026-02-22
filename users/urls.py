# users/urls.py
from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import RegisterView, CustomLoginView, UserListView, UserToggleActiveView



urlpatterns = [
    # Регистрация
    path('register/', RegisterView.as_view(), name='register'),
    # Вход (используем наше кастомное представление)
    path('login/', CustomLoginView.as_view(), name='login'),
    # Выход (стандартное представление Django)
    path('logout/', LogoutView.as_view(), name='logout'),

    path('list/', UserListView.as_view(), name='user_list'),
    path('<int:pk>/toggle-active/', UserToggleActiveView.as_view(), name='user_toggle_active'),
]