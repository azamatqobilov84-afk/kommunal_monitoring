"""
Yordamchi funksiyalar — anomaliya aniqlash, mock SMS, statistika.
"""
import random
import statistics
from decimal import Decimal
from datetime import date, timedelta

from django.utils import timezone

from .models import (
    SmsCode, MeterReading, Anomaly, Notification, Transaction, Service,
)


# ---------- MOCK SMS ----------

def send_mock_sms(phone, purpose='register'):
    """6 xonali kod yaratadi va terminalga chop etadi."""
    code = f'{random.randint(100000, 999999)}'
    SmsCode.objects.create(phone=phone, code=code, purpose=purpose)
    print('=' * 50)
    print(f'📱 [MOCK SMS] Telefon: {phone}')
    print(f'    Tasdiqlash kodi: {code}')
    print(f'    Maqsad: {purpose}')
    print('=' * 50)
    return code


def verify_sms_code(phone, code, purpose='register'):
    sms = SmsCode.objects.filter(
        phone=phone, code=code, purpose=purpose, is_used=False
    ).order_by('-created_at').first()
    if not sms or sms.is_expired():
        return False
    sms.is_used = True
    sms.save()
    return True


# ---------- ANOMALIYA ANIQLASH ----------

def detect_anomalies_for_reading(reading):
    """
    Bitta yangi ko'rsatkich uchun anomaliyalarni aniqlaydi.
    """
    found = []
    meter = reading.meter
    user = meter.property.owner

    # 1) Joriy ko'rsatkich avvalgisidan kichik (xato kiritish)
    if reading.current_value < reading.previous_value:
        a = Anomaly.objects.create(
            user=user, meter=meter, reading=reading,
            title='Hisoblagich yozuvida xatolik',
            description=(f'Joriy ko\'rsatkich ({reading.current_value}) avvalgi '
                         f'ko\'rsatkichdan ({reading.previous_value}) kichik. '
                         f'Yozuvni qayta tekshiring.'),
            severity='high',
        )
        reading.is_anomaly = True
        reading.save(update_fields=['is_anomaly'])
        found.append(a)
        return found

    # 2) Sarfning keskin oshishi (oxirgi 3 oy o'rtachasi + 30%)
    threshold_pct = user.notify_threshold_percent or 30
    last3 = MeterReading.objects.filter(
        meter=meter
    ).exclude(pk=reading.pk).order_by('-reading_date')[:3]

    if last3.count() >= 2:
        consumptions = [float(r.consumption) for r in last3 if r.consumption]
        if consumptions:
            avg = sum(consumptions) / len(consumptions)
            if avg > 0 and float(reading.consumption) > avg * (1 + threshold_pct / 100):
                pct = ((float(reading.consumption) - avg) / avg) * 100
                a = Anomaly.objects.create(
                    user=user, meter=meter, reading=reading,
                    title=f'{meter.service.name} sarfi keskin oshdi',
                    description=(f'Bu oy sarfingiz {reading.consumption} {meter.service.unit} — '
                                 f'oxirgi {last3.count()} oy o\'rtachasidan '
                                 f'{pct:.0f}% ko\'p (o\'rtacha: {avg:.0f}).'),
                    severity='high' if pct > 50 else 'medium',
                )
                reading.is_anomaly = True
                reading.save(update_fields=['is_anomaly'])
                Notification.objects.create(
                    user=user, type='anomaly', icon='bi-exclamation-triangle-fill',
                    title='Anomaliya: yuqori sarf',
                    message=a.description,
                )
                found.append(a)

    # 3) Z-score (5+ yozuv bo'lsa)
    all_readings = MeterReading.objects.filter(meter=meter).exclude(pk=reading.pk)
    if all_readings.count() >= 5:
        consumptions = [float(r.consumption) for r in all_readings if r.consumption]
        if len(consumptions) >= 5:
            try:
                mean = statistics.mean(consumptions)
                stdev = statistics.stdev(consumptions)
                if stdev > 0:
                    z = (float(reading.consumption) - mean) / stdev
                    if abs(z) > 2.5 and not reading.is_anomaly:
                        a = Anomaly.objects.create(
                            user=user, meter=meter, reading=reading,
                            title='Statistik anomaliya',
                            description=(f'Joriy sarf statistik o\'rtachadan {z:+.1f}σ '
                                         f'farq qiladi (g\'ayritabiiy).'),
                            severity='medium',
                        )
                        found.append(a)
            except statistics.StatisticsError:
                pass

    return found


# ---------- STATISTIKA ----------

def monthly_consumption_chart(user, year=None):
    """
    Foydalanuvchining yil bo'yicha oylik xizmat sarflari.
    Qaytaradi: dict {service_name: [12 oy uchun summa]}.
    """
    if not year:
        year = timezone.now().year
    services = Service.objects.all()
    result = {}
    for svc in services:
        amounts = [0] * 12
        readings = MeterReading.objects.filter(
            meter__property__owner=user,
            meter__service=svc,
            reading_date__year=year,
        )
        for r in readings:
            amt = float(r.calculate_amount())
            amounts[r.reading_date.month - 1] += amt
        if any(a > 0 for a in amounts):
            result[svc.name] = {
                'data': [round(a) for a in amounts],
                'color': svc.color,
                'icon': svc.icon,
            }
    return result


def current_month_breakdown(user):
    """Joriy oydagi xizmatlar bo'yicha taqsimot (pie chart uchun)."""
    today = timezone.now().date()
    txs = Transaction.objects.filter(
        user=user, created_at__year=today.year,
        created_at__month=today.month, status='success',
    )
    by_service = {}
    for t in txs:
        if not t.service:
            continue
        by_service.setdefault(t.service.name, {'amount': 0, 'color': t.service.color})
        by_service[t.service.name]['amount'] += float(t.amount)
    return by_service


def total_spent_this_month(user):
    from django.db.models import Sum
    today = timezone.now().date()
    return Transaction.objects.filter(
        user=user, created_at__year=today.year,
        created_at__month=today.month, status='success',
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
