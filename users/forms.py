# users/forms.py
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django import forms

User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    """
    Форма регистрации нового пользователя

    UserCreationForm - стандартная форма Django, которая:
    1. Создает нового пользователя
    2. Проверяет, что пароль и подтверждение пароля совпадают
    3. Хеширует пароль перед сохранением
    """

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Введите email'})
    )

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        """Конструктор формы - добавляет CSS классы Bootstrap ко всем полям"""
        super().__init__(*args, **kwargs)

        # Добавляем классы Bootstrap для красивого отображения
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

            # Добавляем плейсхолдеры (подсказки внутри поля)
            if field_name == 'password1':
                field.widget.attrs['placeholder'] = 'Введите пароль'
            elif field_name == 'password2':
                field.widget.attrs['placeholder'] = 'Подтвердите пароль'

    def save(self, commit=True):
        """
        Переопределяем метод save, чтобы установить username = email
        Потому что в модели User поле username обязательное, но мы его не показываем в форме
        """
        user = super().save(commit=False)
        user.username = user.email  # Устанавливаем username равным email
        if commit:
            user.save()
        return user