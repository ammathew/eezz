from django.core.management.base import BaseCommand
from api.models import DreamSymbol
import os


class Command(BaseCommand):
    help = 'Import dream symbols from dreammoods.txt'

    def handle(self, *args, **options):
        file_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'dreammoods.txt')

        # Clear existing dreammoods data
        DreamSymbol.objects.filter(source='dreammoods').delete()
        self.stdout.write('Cleared existing dreammoods data')

        imported_count = 0

        with open(file_path, 'r', encoding='latin-1') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Split by the pipe delimiter
                parts = [p.strip() for p in line.split('|')]

                if len(parts) < 3:
                    continue

                # First part contains keywords (may have spaces or other delimiters)
                keywords_part = parts[0]
                # Second part is the title (we'll use as primary keyword)
                title = parts[1]

                # Remaining parts are interpretations
                interpretations = [p for p in parts[2:] if p]

                # Create one row per keyword-interpretation pair
                # Use the title as the main keyword
                if title and interpretations:
                    for interpretation in interpretations:
                        if interpretation:
                            DreamSymbol.objects.create(
                                keyword=title,
                                interpretation=interpretation,
                                source='dreammoods'
                            )
                            imported_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully imported {imported_count} dream symbol entries')
        )
