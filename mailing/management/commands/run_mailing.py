from django.core.management.base import BaseCommand
from django.utils import timezone
from mailing.models import Mailing
from mailing.services import send_mailing


class Command(BaseCommand):
    help = 'Запуск рассылки по ID'

    def add_arguments(self, parser):
        parser.add_argument('mailing_id', type=int, help='ID рассылки для запуска')

    def handle(self, *args, **options):
        mailing_id = options['mailing_id']

        try:
            mailing = Mailing.objects.get(id=mailing_id)
        except Mailing.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Рассылка с ID {mailing_id} не найдена')
            )
            return

        self.stdout.write(f'Запуск рассылки: {mailing.name}')
        self.stdout.write(f'Время начала: {mailing.start_time}')
        self.stdout.write(f'Время окончания: {mailing.end_time}')
        self.stdout.write(f'Получателей: {mailing.recipients.count()}')

        # Проверка времени
        now = timezone.now()
        if now < mailing.start_time:
            self.stdout.write(
                self.style.WARNING(f'Рассылка еще не началась. Начало: {mailing.start_time}')
            )
            return
        if now > mailing.end_time:
            self.stdout.write(
                self.style.WARNING(f'Рассылка уже закончилась. Конец: {mailing.end_time}')
            )
            return

        # Запуск отправки
        result = send_mailing(mailing)

        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(f'✅ {result["message"]}')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ {result["message"]}')
            )