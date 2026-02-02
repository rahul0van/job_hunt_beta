"""
Django management command to monitor Google Drive Excel files continuously
"""
from django.core.management.base import BaseCommand
from resume_generator.services import GoogleDriveMonitorService


class Command(BaseCommand):
    help = 'Monitor Google Drive Excel files and automatically generate resumes/cover letters'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Check interval in seconds (default: 60)'
        )
        parser.add_argument(
            '--excel-id',
            type=str,
            help='Google Drive Excel file ID to start monitoring'
        )
        parser.add_argument(
            '--folder-id',
            type=str,
            help='Google Drive folder ID for output documents'
        )
    
    def handle(self, *args, **options):
        check_interval = options['interval']
        excel_id = options.get('excel_id')
        folder_id = options.get('folder_id')
        
        monitor_service = GoogleDriveMonitorService()
        
        # If specific file provided, start monitoring it
        if excel_id and folder_id:
            self.stdout.write(f'Starting to monitor Google Drive file: {excel_id}')
            result = monitor_service.start_monitoring(excel_id, folder_id)
            if not result['success']:
                self.stdout.write(self.style.ERROR(f"Error: {result['error']}"))
                return
            self.stdout.write(self.style.SUCCESS(f"Monitoring started"))
        
        # Display current monitoring status
        status = monitor_service.get_monitoring_status()
        if status['success']:
            self.stdout.write(self.style.SUCCESS(
                f"\nCurrently monitoring {status['active_count']} Google Drive file(s):"
            ))
            for config in status['configs']:
                if config['is_monitoring']:
                    self.stdout.write(f"  ✓ {config['excel_file_name']} (ID: {config['excel_file_id']})")
        
        # Start monitoring loop
        self.stdout.write(f"\nChecking Google Drive every {check_interval} seconds...")
        self.stdout.write("Press Ctrl+C to stop\n")
        
        try:
            monitor_service.monitor_loop(check_interval=check_interval)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nMonitoring stopped by user'))
