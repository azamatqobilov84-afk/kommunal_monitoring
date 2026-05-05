"""
Test ma'lumotlarini avtomatik yaratish.
"""
import random
from decimal import Decimal
from datetime import date, timedelta, datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import (
    User, Property, Service, Tariff, Meter, MeterReading,
    Card, Transaction, Notification, Anomaly,
)
from core.utils import detect_anomalies_for_reading


class Command(BaseCommand):
    help = 'Test ma\'lumotlarini yaratadi'

    def handle(self, *args, **options):
        # Production xavfsizligi: agar baza allaqachon to'ldirilgan bo'lsa — qaytarmaymiz
        from core.models import User
        if User.objects.filter(phone='+998901234567').exists():
            self.stdout.write('⏩ Test ma\'lumotlar allaqachon mavjud — o\'tkazib yuborildi')
            return

        self.stdout.write('🌱 Test ma\'lumotlarini yaratish boshlandi...\n')

        # ------ Xizmatlar ------
        services_data = [
            ('Elektr', 'elektr', 'bi-lightning-charge-fill', '#ffc107', 'kVt·s'),
            ('Gaz', 'gaz', 'bi-fire', '#fd7e14', 'm³'),
            ('Suv', 'suv', 'bi-droplet-fill', '#0dcaf0', 'm³'),
            ('Issiqlik', 'issiqlik', 'bi-thermometer-half', '#dc3545', 'Gkal'),
            ('Internet', 'internet', 'bi-wifi', '#6f42c1', 'Mbit'),
            ('Mobil aloqa', 'mobil', 'bi-phone-fill', '#198754', 'min'),
            ('Avtoyoqilg\'i', 'yoqilgi', 'bi-fuel-pump-fill', '#20c997', 'litr'),
            ('Uy-joy (kvartplata)', 'uy-joy', 'bi-house-door-fill', '#0d6efd', 'm²'),
        ]
        services = {}
        for name, slug, icon, color, unit in services_data:
            s, _ = Service.objects.update_or_create(
                slug=slug,
                defaults={'name': name, 'icon': icon, 'color': color, 'unit': unit,
                          'has_meter': slug in ('elektr', 'gaz', 'suv', 'issiqlik')},
            )
            services[slug] = s
        self.stdout.write(f'  ✓ {len(services)} ta xizmat yaratildi')

        # ------ Tariflar ------
        tariff_data = [
            ('elektr', 'single', 450, 'Toshkent shahri'),
            ('elektr', 'day', 490, 'Toshkent shahri'),
            ('elektr', 'night', 230, 'Toshkent shahri'),
            ('gaz', 'single', 380, 'Toshkent shahri'),
            ('suv', 'single', 1850, 'Toshkent shahri'),
            ('issiqlik', 'single', 25000, 'Toshkent shahri'),
            ('internet', 'single', 80000, 'Toshkent shahri'),
            ('uy-joy', 'single', 5500, 'Toshkent shahri'),
        ]
        for slug, ttype, price, region in tariff_data:
            Tariff.objects.update_or_create(
                service=services[slug], tariff_type=ttype, region=region,
                defaults={'price_per_unit': Decimal(price), 'is_active': True,
                          'valid_from': date(2024, 1, 1)},
            )
        self.stdout.write(f'  ✓ {len(tariff_data)} ta tarif yaratildi')

        # ------ Foydalanuvchilar ------
        users_data = [
            ('+998901234567', 'Akmal', 'Karimov', 'akmal@test.uz',
             'Toshkent sh., Yunusobod, Amir Temur 23-uy', 'Toshkent shahri'),
            ('+998937654321', 'Madina', 'Yusupova', 'madina@test.uz',
             'Toshkent sh., Mirzo Ulug\'bek, Buyuk Ipak Yo\'li 45', 'Toshkent shahri'),
        ]
        users = []
        for phone, fn, ln, email, addr, region in users_data:
            u, created = User.objects.get_or_create(
                phone=phone,
                defaults={'username': phone, 'first_name': fn, 'last_name': ln,
                          'email': email, 'address': addr, 'region': region,
                          'balance': Decimal('1250000')},
            )
            if created:
                u.set_password('parol12345')
                u.save()
            users.append(u)
        self.stdout.write(f'  ✓ {len(users)} ta foydalanuvchi yaratildi')

        # ------ Manzillar ------
        properties_data = [
            (users[0], 'Asosiy uy', 'Toshkent shahri', 'Yunusobod tumani',
             'Bunyodkor', 'Amir Temur', '23', '45', 3, 78, True),
            (users[0], 'Dacha', 'Toshkent viloyati', "Bo'stonliq tumani",
             'Chimyon', 'Tog\' yo\'li', '7', '', 4, 120, False),
            (users[1], 'Asosiy uy', 'Toshkent shahri', "Mirzo Ulug'bek tumani",
             "Buyuk Ipak yo'li", "Buyuk Ipak Yo'li", '45', '12', 2, 54, True),
        ]
        properties = []
        for owner, name, region, district, mahalla, street, house, apt, rooms, area, primary in properties_data:
            p, _ = Property.objects.update_or_create(
                owner=owner, name=name,
                defaults={'region': region, 'district': district,
                          'mahalla': mahalla, 'street': street,
                          'house_number': house, 'apartment': apt,
                          'rooms': rooms, 'area_sqm': area, 'is_primary': primary},
            )
            properties.append(p)
        self.stdout.write(f'  ✓ {len(properties)} ta manzil yaratildi')

        # ------ Hisoblagichlar ------
        meters = []
        for i, prop in enumerate(properties):
            for slug, init_val in [('elektr', 12500), ('gaz', 4200), ('suv', 850)]:
                serial = f'{slug.upper()[:2]}{prop.id:03d}{random.randint(1000, 9999)}'
                m, _ = Meter.objects.update_or_create(
                    property=prop, service=services[slug],
                    defaults={'serial_number': serial,
                              'installed_at': date(2022, random.randint(1, 12),
                                                    random.randint(1, 28)),
                              'tariff_mode': 'single',
                              'initial_reading': Decimal(init_val),
                              'account_number': f'{random.randint(1000000, 9999999)}'},
                )
                meters.append(m)
        self.stdout.write(f'  ✓ {len(meters)} ta hisoblagich yaratildi')

        # ------ Hisoblagich ko'rsatkichlari (12 oy) ------
        today = timezone.now().date()
        readings_count = 0
        for meter in meters:
            current = float(meter.initial_reading)
            for months_ago in range(12, 0, -1):
                # Mavsumiy o'zgarish
                month = (today.month - months_ago - 1) % 12 + 1
                if meter.service.slug == 'elektr':
                    base = 220 + (60 if month in (12, 1, 2, 7, 8) else 0)
                elif meter.service.slug == 'gaz':
                    base = 80 + (120 if month in (12, 1, 2) else 0)
                elif meter.service.slug == 'suv':
                    base = 12 + random.randint(-2, 5)
                else:
                    base = 50

                # Akmalning birinchi uyi uchun bitta sun'iy anomaliya
                if meter.property == properties[0] and meter.service.slug == 'elektr' and months_ago == 2:
                    base = base * 2  # 100% oshib ketgan!

                consumption = base + random.randint(-10, 15)
                reading_date = today - timedelta(days=months_ago * 30)
                prev = current
                current += consumption

                r = MeterReading.objects.create(
                    meter=meter,
                    previous_value=Decimal(prev),
                    current_value=Decimal(current),
                    reading_date=reading_date,
                )
                # Anomaliyalarni aniqlash
                detect_anomalies_for_reading(r)
                readings_count += 1
        self.stdout.write(f'  ✓ {readings_count} ta hisoblagich ko\'rsatkichi yaratildi')

        # ------ Bank kartalari ------
        cards_data = [
            (users[0], 'uzcard', '8600', '1234', 'AKMAL KARIMOV', 12, 2027, 5000000, True),
            (users[0], 'humo', '9860', '5678', 'AKMAL KARIMOV', 6, 2026, 1500000, False),
            (users[0], 'visa', '4276', '9012', 'AKMAL KARIMOV', 3, 2028, 750000, False),
            (users[1], 'uzcard', '8600', '4444', 'MADINA YUSUPOVA', 10, 2027, 3500000, True),
            (users[1], 'humo', '9860', '7777', 'MADINA YUSUPOVA', 8, 2026, 980000, False),
        ]
        cards = []
        for u, ctype, _, last4, holder, em, ey, bal, primary in cards_data:
            c, _ = Card.objects.update_or_create(
                user=u, number_last4=last4,
                defaults={'card_type': ctype, 'holder_name': holder,
                          'expiry_month': em, 'expiry_year': ey,
                          'balance': Decimal(bal), 'is_primary': primary},
            )
            cards.append(c)
        self.stdout.write(f'  ✓ {len(cards)} ta karta yaratildi')

        # ------ Tranzaksiyalar ------
        Transaction.objects.filter(user__in=users).delete()
        tx_count = 0
        for u in users:
            user_props = [p for p in properties if p.owner == u]
            user_cards = [c for c in cards if c.user == u]
            for months_ago in range(6, 0, -1):
                tx_date = today - timedelta(days=months_ago * 30)
                for slug in ['elektr', 'gaz', 'suv']:
                    amount = {'elektr': 95000, 'gaz': 38000, 'suv': 25000}[slug]
                    amount += random.randint(-5000, 15000)
                    Transaction.objects.create(
                        user=u, property=random.choice(user_props),
                        service=services[slug],
                        amount=Decimal(amount), card=random.choice(user_cards),
                        status='success',
                        comment=f'{services[slug].name} oylik to\'lov',
                        created_at=timezone.make_aware(datetime.combine(tx_date, datetime.min.time())),
                    )
                    tx_count += 1
                # Bitta internet to'lovi
                if months_ago % 2 == 0:
                    Transaction.objects.create(
                        user=u, property=user_props[0],
                        service=services['internet'],
                        amount=Decimal(80000), card=random.choice(user_cards),
                        status='success', comment='UzNet — oylik internet',
                        created_at=timezone.make_aware(datetime.combine(tx_date, datetime.min.time())),
                    )
                    tx_count += 1
        self.stdout.write(f'  ✓ {tx_count} ta tranzaksiya yaratildi')

        # ------ Bildirishnomalar ------
        Notification.objects.filter(user__in=users).delete()
        notifs_data = [
            (users[0], 'reminder', 'bi-bell-fill', 'Gazni to\'lash muddati',
             'Gaz uchun to\'lash muddati 5 kun qoldi (25-sana).', False),
            (users[0], 'anomaly', 'bi-exclamation-triangle-fill', 'Yuqori sarf aniqlandi',
             'Bu oy elektr sarfingiz oxirgi 3 oy o\'rtachasidan 80% ortiq.', False),
            (users[0], 'payment', 'bi-check-circle-fill', 'To\'lov muvaffaqiyatli',
             'Suv uchun 25 000 so\'m to\'landi. Kvitansiya: KM-ABC123.', True),
            (users[0], 'tariff', 'bi-info-circle-fill', 'Yangi tarif e\'lon qilindi',
             '1-yanvardan elektr tarifi 450 so\'m/kVt bo\'ladi.', True),
            (users[1], 'reminder', 'bi-bell-fill', 'Hisoblagich kiritmadingiz',
             'Bu oy gaz hisoblagichi ko\'rsatkichini hali kiritmadingiz.', False),
        ]
        for u, t, icon, title, msg, read in notifs_data:
            Notification.objects.create(
                user=u, type=t, icon=icon, title=title, message=msg, is_read=read,
            )
        self.stdout.write(f'  ✓ {len(notifs_data)} ta bildirishnoma yaratildi')

        anomaly_count = Anomaly.objects.filter(user__in=users).count()
        self.stdout.write(f'  ✓ {anomaly_count} ta anomaliya aniqlandi')

        self.stdout.write(self.style.SUCCESS('\n✅ Test ma\'lumotlar tayyor!'))
        self.stdout.write('\nTest foydalanuvchilar:')
        self.stdout.write('  • Akmal Karimov   — telefon: +998901234567, parol: parol12345')
        self.stdout.write('  • Madina Yusupova — telefon: +998937654321, parol: parol12345')
        self.stdout.write('\nAdmin panel uchun: python manage.py createsuperuser\n')
