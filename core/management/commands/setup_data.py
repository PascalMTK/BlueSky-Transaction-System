import bcrypt
from django.core.management.base import BaseCommand
from core.models import Country, User

ACTIVE_CODES = {'ZM', 'CD', 'TZ', 'MW', 'KE', 'ZW', 'ZA', 'NA'}

COUNTRIES = [
    # (name, code, currency_code, currency_name, flag_emoji, phone_code, fee)
    ('Congo (RDC)',         'CD', 'CDF', 'Franc Congolais',     '🇨🇩', '+243', 3.00),
    ('Zambie',              'ZM', 'ZMW', 'Kwacha Zambien',      '🇿🇲', '+260', 3.00),
    ('Tanzanie',            'TZ', 'TZS', 'Shilling Tanzanien',  '🇹🇿', '+255', 3.00),
    ('Malawi',              'MW', 'MWK', 'Kwacha Malawien',     '🇲🇼', '+265', 3.00),
    ('Kenya',               'KE', 'KES', 'Shilling Kenyan',     '🇰🇪', '+254', 3.00),
    ('Zimbabwe',            'ZW', 'USD', 'Dollar US',           '🇿🇼', '+263', 3.00),
    ('Afrique du Sud',      'ZA', 'ZAR', 'Rand',                '🇿🇦', '+27',  3.00),
    ('Namibie',             'NA', 'NAD', 'Dollar Namibien',     '🇳🇦', '+264', 3.00),
    ('Congo (Brazzaville)', 'CG', 'XAF', 'Franc CFA',          '🇨🇬', '+242', 3.00),
    ('Angola',              'AO', 'AOA', 'Kwanza',              '🇦🇴', '+244', 3.00),
    ('Rwanda',              'RW', 'RWF', 'Franc Rwandais',      '🇷🇼', '+250', 3.00),
    ('Burundi',             'BI', 'BIF', 'Franc Burundais',     '🇧🇮', '+257', 3.00),
    ('Uganda',              'UG', 'UGX', 'Shilling Ougandais',  '🇺🇬', '+256', 3.00),
    ('Cameroun',            'CM', 'XAF', 'Franc CFA',           '🇨🇲', '+237', 3.00),
    ('Gabon',               'GA', 'XAF', 'Franc CFA',           '🇬🇦', '+241', 3.00),
    ('Sénégal',             'SN', 'XOF', 'Franc CFA',           '🇸🇳', '+221', 3.00),
    ("Côte d'Ivoire",       'CI', 'XOF', 'Franc CFA',           '🇨🇮', '+225', 3.00),
    ('France',              'FR', 'EUR', 'Euro',                 '🇫🇷', '+33',  3.00),
    ('Belgique',            'BE', 'EUR', 'Euro',                 '🇧🇪', '+32',  3.00),
    ('USA',                 'US', 'USD', 'Dollar US',            '🇺🇸', '+1',   3.00),
    ('Canada',              'CA', 'CAD', 'Dollar Canadien',      '🇨🇦', '+1',   3.00),
    ('Chine',               'CN', 'CNY', 'Yuan',                 '🇨🇳', '+86',  3.00),
]


class Command(BaseCommand):
    help = 'Create initial countries and admin user'

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for name, code, currency_code, currency_name, flag, phone_code, fee in COUNTRIES:
            is_active = code in ACTIVE_CODES
            obj, was_created = Country.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'currency_code': currency_code,
                    'currency_name': currency_name,
                    'flag_emoji': flag,
                    'phone_code': phone_code,
                    'default_fee_percentage': fee,
                    'is_active': is_active,
                }
            )
            if not was_created:
                obj.name = name
                obj.flag_emoji = flag
                obj.is_active = is_active
                obj.save()
                updated += 1
            else:
                created += 1

        active_count = Country.objects.filter(is_active=True).count()
        self.stdout.write(self.style.SUCCESS(
            f'✓ Pays : {created} créés, {updated} mis à jour — {active_count} actifs'
        ))

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
            self.stdout.write(self.style.SUCCESS(
                '✓ Admin créé → email: admin@bluesky.com  |  mot de passe: Admin2026!'
            ))
        else:
            self.stdout.write(self.style.WARNING('! Admin existe déjà'))
