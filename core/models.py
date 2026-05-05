"""
Kommunal to'lovlar monitoringi — barcha ma'lumotlar modellari.
"""
from decimal import Decimal
from datetime import date, timedelta
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


# ---------- FOYDALANUVCHI ----------

class User(AbstractUser):
    """
    Click stilida — telefon raqami username sifatida ishlatiladi.
    """
    phone = models.CharField('Telefon', max_length=20, unique=True)
    address = models.CharField('Manzil', max_length=255, blank=True)
    region = models.CharField('Hudud', max_length=100, blank=True, default='Toshkent shahri')
    avatar = models.ImageField('Avatar', upload_to='avatars/', blank=True, null=True)
    balance = models.DecimalField('Balans (so\'m)', max_digits=12, decimal_places=2,
                                   default=Decimal('1250000.00'))
    pin_code = models.CharField('PIN kod', max_length=4, blank=True)
    notify_threshold_percent = models.IntegerField(
        'Sarflash ogohlantirish chegarasi (%)', default=30
    )
    language = models.CharField('Til', max_length=10, default='uz', choices=[
        ('uz', 'O\'zbek (lotin)'), ('uz-cyrl', 'O\'zbek (kirill)'),
        ('ru', 'Русский'), ('en', 'English'),
    ])

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.phone})'

    @property
    def display_name(self):
        return self.get_full_name() or self.phone

    def initials(self):
        if self.first_name and self.last_name:
            return (self.first_name[0] + self.last_name[0]).upper()
        return (self.phone[-2:] if self.phone else 'KM').upper()


# ---------- XIZMATLAR VA TARIFLAR ----------

class Service(models.Model):
    """Kommunal xizmat turi: gaz, elektr, suv va h.k."""
    name = models.CharField('Nomi', max_length=80)
    slug = models.SlugField('Slug', unique=True)
    icon = models.CharField('Bootstrap Icon nomi', max_length=50, default='bi-lightning')
    color = models.CharField('HEX rang', max_length=7, default='#0066ff')
    unit = models.CharField('O\'lchov birligi', max_length=20, default='kVt·s')
    has_meter = models.BooleanField('Hisoblagichli', default=True)
    description = models.CharField('Tavsif', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Xizmat'
        verbose_name_plural = 'Xizmatlar'
        ordering = ['name']

    def __str__(self):
        return self.name


class Tariff(models.Model):
    """Bir xizmat uchun tarif rejasi (vaqt va hudud bo'yicha)."""
    TARIFF_TYPE = (
        ('single', 'Bir vaqtli'),
        ('day', 'Kunduzgi'),
        ('night', 'Tungi'),
    )
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='tariffs',
                                verbose_name='Xizmat')
    name = models.CharField('Nomi', max_length=80, blank=True)
    tariff_type = models.CharField('Turi', max_length=10, choices=TARIFF_TYPE, default='single')
    region = models.CharField('Hudud', max_length=100, default='Toshkent shahri')
    price_per_unit = models.DecimalField('Birlik narxi (so\'m)', max_digits=10, decimal_places=2)
    valid_from = models.DateField('Boshlangan sana', default=date.today)
    valid_to = models.DateField('Tugagan sana', null=True, blank=True)
    is_active = models.BooleanField('Faol', default=True)

    class Meta:
        verbose_name = 'Tarif'
        verbose_name_plural = 'Tariflar'
        ordering = ['service', '-valid_from']

    def __str__(self):
        return f'{self.service.name} — {self.get_tariff_type_display()} — {self.price_per_unit} so\'m'


# ---------- MANZIL VA HISOBLAGICHLAR ----------

class Property(models.Model):
    """Foydalanuvchining uy/kvartira/dachasi."""
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties',
                              verbose_name='Egasi')
    name = models.CharField('Nomi', max_length=100, help_text='Masalan: "Asosiy uy"')
    # Tuzilgan manzil — Click stilida
    region = models.CharField('Viloyat', max_length=100, default='Toshkent shahri')
    district = models.CharField('Tuman/Shahar', max_length=100, blank=True)
    mahalla = models.CharField('Mahalla / MFY', max_length=150, blank=True)
    street = models.CharField("Ko'cha", max_length=150, blank=True)
    house_number = models.CharField('Uy raqami', max_length=20, blank=True)
    apartment = models.CharField('Kvartira raqami', max_length=20, blank=True)
    # Toliq manzil — avtomatik to'ldiriladi
    address = models.CharField("To'liq manzil", max_length=500, blank=True)
    rooms = models.IntegerField('Xonalar soni', default=2)
    area_sqm = models.DecimalField('Maydoni (m²)', max_digits=6, decimal_places=2, default=60)
    is_primary = models.BooleanField('Asosiy', default=False)
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)

    class Meta:
        verbose_name = 'Manzil'
        verbose_name_plural = 'Manzillar'
        ordering = ['-is_primary', '-created_at']

    def __str__(self):
        return f'{self.name} — {self.full_address()}'

    def save(self, *args, **kwargs):
        # To'liq manzilni avtomatik yig'ish
        if not self.address or self._state.adding:
            self.address = self.full_address()
        super().save(*args, **kwargs)

    def full_address(self):
        """Tuzilgan maydonlardan to'liq manzil yig'adi."""
        parts = []
        if self.region:
            parts.append(self.region)
        if self.district:
            parts.append(self.district)
        if self.mahalla:
            parts.append(f'{self.mahalla} MFY')
        if self.street:
            parts.append(f"{self.street} ko'chasi")
        if self.house_number:
            hn = f'{self.house_number}-uy'
            if self.apartment:
                hn += f', {self.apartment}-xona'
            parts.append(hn)
        return ', '.join(parts) if parts else (self.address or '')


class Meter(models.Model):
    """Hisoblagich (elektr/gaz/suv...)."""
    TARIFF_MODE = (
        ('single', 'Bir vaqtli (oddiy)'),
        ('double', 'Ikki vaqtli (kun/tun)'),
    )
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='meters',
                                 verbose_name='Manzil')
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='meters',
                                verbose_name='Xizmat')
    serial_number = models.CharField('Seriya raqami', max_length=50)
    installed_at = models.DateField('O\'rnatilgan sana', default=date.today)
    tariff_mode = models.CharField('Tarif rejimi', max_length=10, choices=TARIFF_MODE,
                                   default='single')
    initial_reading = models.DecimalField('Boshlang\'ich ko\'rsatkich', max_digits=10,
                                           decimal_places=2, default=0)
    is_active = models.BooleanField('Faol', default=True)
    account_number = models.CharField('Shaxsiy hisob raqami', max_length=30, blank=True)

    class Meta:
        verbose_name = 'Hisoblagich'
        verbose_name_plural = 'Hisoblagichlar'

    def __str__(self):
        return f'{self.service.name} #{self.serial_number} — {self.property.name}'

    def last_reading(self):
        return self.readings.order_by('-reading_date').first()

    def current_value(self):
        last = self.last_reading()
        return last.current_value if last else self.initial_reading


class MeterReading(models.Model):
    """Hisoblagich ko'rsatkichi yozuvi."""
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, related_name='readings',
                              verbose_name='Hisoblagich')
    previous_value = models.DecimalField('Avvalgi ko\'rsatkich', max_digits=10, decimal_places=2)
    current_value = models.DecimalField('Joriy ko\'rsatkich', max_digits=10, decimal_places=2)
    consumption = models.DecimalField('Sarfi', max_digits=10, decimal_places=2, default=0)
    night_consumption = models.DecimalField('Tungi sarf', max_digits=10, decimal_places=2,
                                             default=0, help_text='Faqat 2 vaqtli tarifda')
    reading_date = models.DateField('Sana', default=date.today)
    image = models.ImageField('Hisoblagich rasmi', upload_to='meter_readings/',
                              blank=True, null=True)
    note = models.CharField('Izoh', max_length=200, blank=True)
    is_anomaly = models.BooleanField('Anomaliya', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Hisoblagich ko\'rsatkichi'
        verbose_name_plural = 'Hisoblagich ko\'rsatkichlari'
        ordering = ['-reading_date', '-created_at']

    def __str__(self):
        return f'{self.meter} — {self.reading_date} ({self.consumption})'

    def save(self, *args, **kwargs):
        # Sarfni avtomatik hisoblash
        try:
            self.consumption = self.current_value - self.previous_value
        except Exception:
            self.consumption = 0
        super().save(*args, **kwargs)

    def calculate_amount(self):
        """Tarifga ko'ra to'lash summasi."""
        from django.utils import timezone
        today = timezone.now().date()
        tariff = Tariff.objects.filter(
            service=self.meter.service,
            region=self.meter.property.region,
            tariff_type='single',
            is_active=True,
            valid_from__lte=self.reading_date,
        ).order_by('-valid_from').first()
        if not tariff:
            tariff = self.meter.service.tariffs.filter(is_active=True).first()
        if not tariff:
            return Decimal('0')
        return (self.consumption or Decimal('0')) * tariff.price_per_unit


# ---------- BANK KARTALARI ----------

class Card(models.Model):
    """Mock bank kartasi."""
    CARD_TYPE = (
        ('uzcard', 'UzCard'),
        ('humo', 'Humo'),
        ('visa', 'Visa'),
        ('mastercard', 'MasterCard'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards',
                             verbose_name='Egasi')
    card_type = models.CharField('Turi', max_length=15, choices=CARD_TYPE, default='uzcard')
    number_last4 = models.CharField('Oxirgi 4 raqam', max_length=4)
    holder_name = models.CharField('Egasining ismi', max_length=100)
    expiry_month = models.IntegerField('Amal qilish oyi')
    expiry_year = models.IntegerField('Amal qilish yili')
    balance = models.DecimalField('Balans (so\'m)', max_digits=12, decimal_places=2,
                                   default=Decimal('5000000'))
    is_primary = models.BooleanField('Asosiy', default=False)
    is_active = models.BooleanField('Faol', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Karta'
        verbose_name_plural = 'Kartalar'
        ordering = ['-is_primary', '-created_at']

    def __str__(self):
        return f'{self.get_card_type_display()} •••• {self.number_last4}'

    def masked_number(self):
        return f'•••• •••• •••• {self.number_last4}'

    def expiry_str(self):
        return f'{self.expiry_month:02d}/{str(self.expiry_year)[-2:]}'


# ---------- TRANZAKSIYALAR ----------

class Transaction(models.Model):
    """To'lov yozuvi."""
    STATUS = (
        ('success', 'Muvaffaqiyatli'),
        ('pending', 'Kutilmoqda'),
        ('failed', 'Bekor qilingan'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions',
                             verbose_name='Foydalanuvchi')
    property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='transactions', verbose_name='Manzil')
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='transactions', verbose_name='Xizmat')
    amount = models.DecimalField('Summa (so\'m)', max_digits=12, decimal_places=2)
    card = models.ForeignKey(Card, on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name='Karta')
    status = models.CharField('Holat', max_length=10, choices=STATUS, default='success')
    receipt_number = models.CharField('Kvitansiya raqami', max_length=20, unique=True)
    comment = models.CharField('Izoh', max_length=255, blank=True)
    account_number = models.CharField('Shaxsiy hisob', max_length=30, blank=True)
    is_auto = models.BooleanField('Avtomatik to\'lov', default=False)
    created_at = models.DateTimeField('Sana', default=timezone.now)

    class Meta:
        verbose_name = 'Tranzaksiya'
        verbose_name_plural = 'Tranzaksiyalar'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.receipt_number} — {self.amount} so\'m'

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = 'KM' + uuid.uuid4().hex[:10].upper()
        super().save(*args, **kwargs)


# ---------- BILDIRISHNOMALAR ----------

class Notification(models.Model):
    """Foydalanuvchi bildirishnomalari."""
    TYPE = (
        ('payment', 'To\'lov'),
        ('reminder', 'Eslatma'),
        ('anomaly', 'Anomaliya'),
        ('tariff', 'Tarif'),
        ('system', 'Tizim'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications',
                             verbose_name='Foydalanuvchi')
    title = models.CharField('Sarlavha', max_length=150)
    message = models.TextField('Matn')
    type = models.CharField('Turi', max_length=15, choices=TYPE, default='system')
    icon = models.CharField('Ikon', max_length=50, default='bi-bell')
    is_read = models.BooleanField('O\'qilgan', default=False)
    link = models.CharField('Havola', max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Bildirishnoma'
        verbose_name_plural = 'Bildirishnomalar'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.user})'


# ---------- ESLATMALAR VA AVTO-TO'LOVLAR ----------

class Reminder(models.Model):
    """To'lov eslatmasi."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminders',
                             verbose_name='Foydalanuvchi')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name='Xizmat')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, null=True, blank=True,
                                 verbose_name='Manzil')
    day_of_month = models.IntegerField('Oyning kuni', default=25)
    message = models.CharField('Xabar', max_length=200, blank=True)
    is_active = models.BooleanField('Faol', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Eslatma'
        verbose_name_plural = 'Eslatmalar'

    def __str__(self):
        return f'{self.service.name} — har oyning {self.day_of_month}-sanasi'


class AutoPayment(models.Model):
    """Avtomatik to'lov rejasi."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auto_payments',
                             verbose_name='Foydalanuvchi')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name='Xizmat')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, verbose_name='Manzil')
    card = models.ForeignKey(Card, on_delete=models.SET_NULL, null=True, verbose_name='Karta')
    day_of_month = models.IntegerField('Oyning kuni', default=10)
    max_amount = models.DecimalField('Maksimal summa', max_digits=12, decimal_places=2,
                                      default=Decimal('500000'))
    is_active = models.BooleanField('Faol', default=True)
    last_run = models.DateField('Oxirgi ishga tushgan', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Avtomatik to\'lov'
        verbose_name_plural = 'Avtomatik to\'lovlar'

    def __str__(self):
        return f'{self.service.name} — {self.property.name} — har oyning {self.day_of_month}-i'


# ---------- ANOMALIYA ----------

class Anomaly(models.Model):
    """Aniqlangan anomaliya."""
    SEVERITY = (
        ('low', 'Past'),
        ('medium', 'O\'rta'),
        ('high', 'Yuqori'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='anomalies',
                             verbose_name='Foydalanuvchi')
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, null=True, blank=True,
                              verbose_name='Hisoblagich')
    reading = models.ForeignKey(MeterReading, on_delete=models.CASCADE, null=True, blank=True,
                                 verbose_name='Yozuv')
    title = models.CharField('Sarlavha', max_length=150)
    description = models.TextField('Tavsif')
    severity = models.CharField('Darajasi', max_length=10, choices=SEVERITY, default='medium')
    is_resolved = models.BooleanField('Hal qilingan', default=False)
    detected_at = models.DateTimeField('Aniqlangan', auto_now_add=True)

    class Meta:
        verbose_name = 'Anomaliya'
        verbose_name_plural = 'Anomaliyalar'
        ordering = ['-detected_at']

    def __str__(self):
        return f'{self.title} — {self.user}'


# ---------- OILA ----------

class FamilyMember(models.Model):
    """Oila a'zosi (bir manzilga kirish huquqi)."""
    ROLE = (
        ('viewer', 'Faqat ko\'rish'),
        ('editor', 'Tahrirlash'),
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='family_invites',
                              verbose_name='Egasi')
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='family_member_in',
                               verbose_name='A\'zo')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='family_members',
                                 verbose_name='Manzil')
    role = models.CharField('Rol', max_length=10, choices=ROLE, default='viewer')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Oila a\'zosi'
        verbose_name_plural = 'Oila a\'zolari'
        unique_together = ('member', 'property')

    def __str__(self):
        return f'{self.member} — {self.property.name} ({self.get_role_display()})'


# ---------- SMS TASDIQLASH (mock) ----------

class SmsCode(models.Model):
    """Mock SMS tasdiqlash kodi."""
    PURPOSE = (
        ('register', 'Ro\'yxatdan o\'tish'),
        ('reset', 'Parol tiklash'),
        ('confirm', 'Tasdiqlash'),
    )
    phone = models.CharField('Telefon', max_length=20)
    code = models.CharField('Kod', max_length=6)
    purpose = models.CharField('Maqsad', max_length=10, choices=PURPOSE, default='register')
    is_used = models.BooleanField('Ishlatilgan', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'SMS kod'
        verbose_name_plural = 'SMS kodlar'
        ordering = ['-created_at']

    def is_expired(self):
        return self.created_at < timezone.now() - timedelta(minutes=10)

    def __str__(self):
        return f'{self.phone} — {self.code}'
