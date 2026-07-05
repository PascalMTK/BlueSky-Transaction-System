import os
import zipfile
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings


class Command(BaseCommand):
    help = 'Backup all core data (users, countries, transactions, reports) and uploaded media into timestamped archives'

    def add_arguments(self, parser):
        parser.add_argument('--keep', type=int, default=7, help='Number of recent backups to keep per type (default: 7)')

    def handle(self, *args, **options):
        backup_dir = settings.BASE_DIR / 'backups'
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 1. Data dump (JSON) — portable across SQLite/MySQL, easy to inspect/restore
        data_path = backup_dir / f'data_{timestamp}.json'
        with open(data_path, 'w', encoding='utf-8') as f:
            call_command('dumpdata', 'core', indent=2, stdout=f)
        self.stdout.write(self.style.SUCCESS(f'✓ Données exportées : {data_path.name} ({data_path.stat().st_size // 1024} Ko)'))

        # 2. Uploaded media (profile photos) — zipped
        media_root = settings.MEDIA_ROOT
        if os.path.isdir(media_root) and os.listdir(media_root):
            media_zip_path = backup_dir / f'media_{timestamp}.zip'
            with zipfile.ZipFile(media_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(media_root):
                    for file in files:
                        full_path = os.path.join(root, file)
                        arcname = os.path.relpath(full_path, media_root)
                        zf.write(full_path, arcname)
            self.stdout.write(self.style.SUCCESS(f'✓ Médias archivés : {media_zip_path.name} ({media_zip_path.stat().st_size // 1024} Ko)'))
        else:
            self.stdout.write('— Aucun fichier média à archiver.')

        # 3. Rotate old backups — keep only the most recent N of each type
        keep = options['keep']
        for pattern in ('data_*.json', 'media_*.zip'):
            files = sorted(backup_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
            for old in files[keep:]:
                old.unlink()
                self.stdout.write(f'🗑 Ancienne sauvegarde supprimée : {old.name}')

        self.stdout.write(self.style.SUCCESS(f'\n✅ Sauvegarde terminée dans {backup_dir}'))
