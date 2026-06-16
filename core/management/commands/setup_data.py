import bcrypt
from django.core.management.base import BaseCommand
from core.models import Country, User


COUNTRIES = [
    ('Congo (RDC)',        'CD', 'CDF', 'Franc Congolais',    '🇨🇩', '+243', 3.00),
    ('Congo (Brazzaville)','CG', 'XAF', 'Franc CFA',         '🇨🇬', '+242', 3.00),
    ('Angola',             'AO', 'AOA', 'Kwanza',             '🇦🇴', '+244', 3.00),
    ('Rwanda',             'RW', 'RWF', 'Franc Rwandais',     '🇷🇼', '+250', 3.00),
    ('Burundi',            'BI', 'BIF', 'Franc Burundais',    '🇧🇮', '+257', 3.00),
    ('Uganda',             'UG', 'UGX', 'Shilling Ougandais', '🇺🇬', '+256', 3.00),
    ('Kenya',              'KE', 'KES', 'Shilling Kenyan',    '🇰🇪', '+254', 3.00),
    ('Tanzania',           'TZ', 'TZS', 'Shilling Tanzanien', '🇹🇿', '+255', 3.00),
    ('Zambia',             'ZM', 'ZMW', 'Kwacha Zambien',     '🇿🇲', '+260', 3.00),
    ('Zimbabwe',           'ZW', 'USD', 'Dollar US',          '🇿🇼', '+263', 3.00),
    ('South Africa',       'ZA', 'ZAR', 'Rand',               '🇿🇦', '+27',  3.00),
    ('Cameroun',           'CM', 'XAF', 'Franc CFA',          '🇨🇲', '+237', 3.00),
    ('Gabon',              'GA', 'XAF', 'Franc CFA',          '🇬🇦', '+241', 3.00),
    ('Sénégal',            'SN', 'XOF', 'Franc CFA',          '🇸🇳', '+221', 3.00),
    ('Côte d\'Ivoire',     'CI', 'XOF', 'Franc CFA',          '🇨🇮', '+225', 3.00),
    ('France',             'FR', 'EUR', 'Euro',                '🇫🇷', '+33',  3.00),
    ('Belgique',           'BE', 'EUR', 'Euro',                '🇧🇪', '+32',  3.00),
    ('USA',                'US', 'USD', 'Dollar US',           '🇺🇸', '+1',   3.00),
    ('Canada',             'CA', 'CAD', 'Dollar Canadien',     '🇨🇦', '+1',   3.00),
    ('Chine',              'CN', 'CNY', 'Yuan',                '🇨🇳', '+86',  3.00),
]


class Command(BaseCommand):
    help = 'Create initial countries and admin user'

    def handle(self, *args, **options):
        # Countries
        created_count = 0
        for name, code, currency_code, currency_name, flag, phone_code, fee in COUNTRIES:
            _, created = Country.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'currency_code': currency_code,
                    'currency_name': currency_name,
                    'flag_emoji': flag,
                    'phone_code': phone_code,
                    'default_fee_percentage': fee,
                    'is_active': True,
                }
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'✓ {created_count} pays créés ({Country.objects.count()} total)'))

        # Admin user
        if not User.objects.filter(email='admin@bluesky.com').exists():
            hashed = bcrypt.hashpw(b'Admin2026!', bcrypt.gensalt(10)).decode()
            User.objects.create(
                name='Administrateur',
                email='admin@bluesky.com',
                password=hashed,
                role='admin',
                status='active',
                agent_code='ADMIN001',
            )
            self.stdout.write(self.style.SUCCESS('✓ Admin créé → email: admin@bluesky.com  |  mot de passe: Admin2026!'))
        else:
            self.stdout.write(self.style.WARNING('! Admin existe déjà'))
