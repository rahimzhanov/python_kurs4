# mailing/services.py
import smtplib
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Attempt


def send_mailing(mailing):
    """
    Функция для отправки рассылки

    Аргументы:
        mailing - объект рассылки (Mailing)

    Что делает:
    1. Проверяет, можно ли отправлять (время между start_time и end_time)
    2. Для каждого получателя отправляет письмо
    3. Сохраняет результат в Attempt
    4. Возвращает статистику отправки
    """

    # Шаг 1: Проверяем время
    now = timezone.now()
    if now < mailing.start_time:
        return {
            'success': False,
            'message': f'Рассылка еще не началась. Начало: {mailing.start_time}'
        }
    if now > mailing.end_time:
        return {
            'success': False,
            'message': f'Рассылка уже закончилась. Конец: {mailing.end_time}'
        }

    # Шаг 2: Проверяем активность
    if not mailing.is_active:
        return {
            'success': False,
            'message': 'Рассылка не активна'
        }

    # Шаг 3: Получаем всех получателей
    recipients = mailing.recipients.all()
    if not recipients:
        return {
            'success': False,
            'message': 'Нет получателей для рассылки'
        }

    # Шаг 4: Отправляем письма каждому получателю
    success_count = 0
    failed_count = 0
    results = []

    for recipient in recipients:
        try:
            # Пытаемся отправить письмо
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )

            # Если успешно - сохраняем Attempt со статусом success
            Attempt.objects.create(
                mailing=mailing,
                status='success',
                recipient_email=recipient.email,
                server_response='OK'
            )
            success_count += 1
            results.append({
                'email': recipient.email,
                'status': 'success'
            })

        except Exception as e:
            # Если ошибка - сохраняем Attempt со статусом failed
            Attempt.objects.create(
                mailing=mailing,
                status='failed',
                recipient_email=recipient.email,
                error_message=str(e),
                server_response='Error'
            )
            failed_count += 1
            results.append({
                'email': recipient.email,
                'status': 'failed',
                'error': str(e)
            })

    # Шаг 5: Возвращаем результат
    return {
        'success': True,
        'total': len(recipients),
        'success_count': success_count,
        'failed_count': failed_count,
        'results': results,
        'message': f'Отправлено: {success_count}, ошибок: {failed_count}'
    }