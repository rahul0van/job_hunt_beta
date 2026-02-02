"""
Management command to start continuous Google Drive monitoring
"""
from django.core.management.base import BaseCommand
from resume_generator.services.google_drive_monitor_service import GoogleDriveMonitorService


class Command(BaseCommand):
    help = 'Start continuous Google Drive monitoring for job applications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Check interval in seconds (default: 60)',
        )

    def handle(self, *args, **options):
        interval = options['interval']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting Google Drive monitoring (checking every {interval} seconds)...\n'
                'Press Ctrl+C to stop\n'
            )
        )
        
        monitor = GoogleDriveMonitorService()
        monitor.monitor_loop(check_interval=interval)
