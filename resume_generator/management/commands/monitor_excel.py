"""
Django management command to monitor Excel files continuously
"""
from django.core.management.base import BaseCommand
from resume_generator.excel_monitor_service import ExcelMonitorService


class Command(BaseCommand):
    help = 'Monitor Excel files and automatically generate resumes/cover letters'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Check interval in seconds (default: 60)'
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Specific Excel file to monitor (optional)'
        )
    
    def handle(self, *args, **options):
        check_interval = options['interval']
        file_path = options.get('file')
        
        monitor_service = ExcelMonitorService()
        
        # If specific file provided, start monitoring it
        if file_path:
            self.stdout.write(f'Starting to monitor: {file_path}')
            result = monitor_service.start_monitoring(file_path)
            if not result['success']:
                self.stdout.write(self.style.ERROR(f"Error: {result['error']}"))
                return
            self.stdout.write(self.style.SUCCESS(f"Monitoring started: {file_path}"))
        
        # Display current monitoring status
        status = monitor_service.get_monitoring_status()
        if status['success']:
            self.stdout.write(self.style.SUCCESS(
                f"\nCurrently monitoring {status['active_count']} file(s):"
            ))
            for tracker in status['trackers']:
                if tracker['is_monitoring']:
                    exists = "✓" if tracker['file_exists'] else "✗"
                    self.stdout.write(f"  [{exists}] {tracker['file_path']}")
        
        # Start monitoring loop
        self.stdout.write(f"\nChecking every {check_interval} seconds...")
        self.stdout.write("Press Ctrl+C to stop\n")
        
        try:
            monitor_service.monitor_loop(check_interval=check_interval)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nMonitoring stopped by user'))
