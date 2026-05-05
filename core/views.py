"""
Barcha sahifalar uchun viewlar.
"""
import csv
import json
from decimal import Decimal
from datetime import datetime, timedelta, date

from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q, Avg, F
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    PhoneRegisterForm, SmsConfirmForm, LoginForm,
    PasswordResetPhoneForm, PasswordResetConfirmForm,
    PropertyForm, MeterForm, MeterReadingForm, CardForm,
    PaymentForm, ReminderForm, AutoPaymentForm, ProfileForm,
    ChangePasswordForm, FamilyInviteForm, normalize_phone,
)
from .models import (
    User, Property, Service, Tariff, Meter, MeterReading, Card,
    Transaction, Notification, Reminder, AutoPayment, Anomaly,
    FamilyMember,
)
from .utils import (
    send_mock_sms, verify_sms_code, detect_anomalies_for_reading,
    monthly_consumption_chart, current_month_breakdown,
)
from .locations import UZBEKISTAN_LOCATIONS, get_districts


# ============ API ============

def api_districts(request):
    """JS uchun: viloyat berilsa — uning tumanlarini JSON qaytaradi."""
    region = request.GET.get('region', '')
    districts = get_districts(region)
    return JsonResponse({'districts': districts})


# ============ LANDING / AUTH ============

def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')


def register_phone(request):
    if request.method == 'POST':
        form = PhoneRegisterForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            send_mock_sms(phone, purpose='register')
            request.session['register_phone'] = phone
            messages.info(request, f'Tasdiqlash kodi {phone} raqamiga yuborildi. '
                                   'Kodni terminalga qarang (mock rejim).')
            return redirect('register_confirm')
    else:
        form = PhoneRegisterForm()
    return render(request, 'auth/register_phone.html', {'form': form})


def register_confirm(request):
    phone = request.session.get('register_phone')
    if not phone:
        return redirect('register')
    if request.method == 'POST':
        form = SmsConfirmForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            if not verify_sms_code(phone, code, purpose='register'):
                messages.error(request, 'Kod noto\'g\'ri yoki muddati tugagan.')
            else:
                u = User.objects.create_user(
                    username=phone, phone=phone,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    password=form.cleaned_data['password'],
                )
                login(request, u)
                Notification.objects.create(
                    user=u, type='system', icon='bi-check-circle-fill',
                    title='Xush kelibsiz!',
                    message='Tizimga muvaffaqiyatli ro\'yxatdan o\'tdingiz. '
                            'Keling, birinchi manzilingizni qo\'shamiz.',
                    link='/properties/new/',
                )
                request.session.pop('register_phone', None)
                messages.success(request, 'Ro\'yxatdan o\'tish muvaffaqiyatli!')
                return redirect('dashboard')
    else:
        form = SmsConfirmForm()
    return render(request, 'auth/register_confirm.html', {'form': form, 'phone': phone})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            password = form.cleaned_data['password']
            user = authenticate(request, username=phone, password=password)
            if not user:
                # username field uchun fallback
                try:
                    u = User.objects.get(phone=phone)
                    if u.check_password(password):
                        user = u
                except User.DoesNotExist:
                    user = None
            if user:
                login(request, user)
                return redirect('dashboard')
            messages.error(request, 'Telefon raqami yoki parol noto\'g\'ri.')
    else:
        form = LoginForm()
    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('landing')


def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetPhoneForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            send_mock_sms(phone, purpose='reset')
            request.session['reset_phone'] = phone
            messages.info(request, 'Tasdiqlash kodi yuborildi (terminalga qarang).')
            return redirect('password_reset_confirm')
    else:
        form = PasswordResetPhoneForm()
    return render(request, 'auth/password_reset.html', {'form': form})


def password_reset_confirm(request):
    phone = request.session.get('reset_phone')
    if not phone:
        return redirect('password_reset')
    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            if not verify_sms_code(phone, code, purpose='reset'):
                messages.error(request, 'Kod noto\'g\'ri yoki muddati tugagan.')
            else:
                u = User.objects.get(phone=phone)
                u.set_password(form.cleaned_data['new_password'])
                u.save()
                request.session.pop('reset_phone', None)
                messages.success(request, 'Parol muvaffaqiyatli yangilandi. Endi kiring.')
                return redirect('login')
    else:
        form = PasswordResetConfirmForm()
    return render(request, 'auth/password_reset_confirm.html', {'form': form, 'phone': phone})


# ============ DASHBOARD ============

@login_required
def dashboard(request):
    user = request.user
    today = timezone.now().date()

    # Joriy oy xarajatlari
    current_total = Transaction.objects.filter(
        user=user, status='success',
        created_at__year=today.year, created_at__month=today.month,
    ).aggregate(s=Sum('amount'))['s'] or Decimal('0')

    # Oxirgi 5 ta tranzaksiya
    last_txs = Transaction.objects.filter(user=user).select_related('service', 'property')[:5]

    # Eslatmalar — yaqinlashayotgan
    upcoming_reminders = []
    for r in Reminder.objects.filter(user=user, is_active=True):
        days_left = (r.day_of_month - today.day) % 30
        if days_left <= 7:
            upcoming_reminders.append({
                'reminder': r, 'days_left': days_left if days_left else 0,
            })

    # Ochiq anomaliyalar
    anomalies = Anomaly.objects.filter(user=user, is_resolved=False)[:3]

    # Dashboard chart — joriy oy taqsimoti
    breakdown = current_month_breakdown(user)

    # Tezkor amallar — barcha xizmatlar
    services = Service.objects.all()

    # Manzillar
    properties = Property.objects.filter(owner=user)

    # Hisoblagichlar — kiritilmagan oylar uchun ogohlantirish
    pending_meters = []
    for m in Meter.objects.filter(property__owner=user, is_active=True):
        last = m.last_reading()
        if not last or (today - last.reading_date).days > 30:
            pending_meters.append(m)

    context = {
        'current_total': current_total,
        'last_txs': last_txs,
        'upcoming_reminders': upcoming_reminders,
        'anomalies': anomalies,
        'breakdown_json': json.dumps([
            {'name': k, 'amount': v['amount'], 'color': v['color']}
            for k, v in breakdown.items()
        ]),
        'has_breakdown': bool(breakdown),
        'services': services,
        'properties': properties,
        'pending_meters': pending_meters,
    }
    return render(request, 'dashboard.html', context)


# ============ PROPERTIES ============

@login_required
def properties_list(request):
    properties = Property.objects.filter(owner=request.user).prefetch_related('meters')
    return render(request, 'properties/list.html', {'properties': properties})


@login_required
def property_new(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            p.owner = request.user
            if p.is_primary:
                Property.objects.filter(owner=request.user).update(is_primary=False)
            p.save()
            messages.success(request, f'"{p.name}" qo\'shildi.')
            return redirect('property_detail', pk=p.pk)
    else:
        form = PropertyForm(initial={'is_primary': not Property.objects.filter(owner=request.user).exists()})
    return render(request, 'properties/form.html', {'form': form, 'is_new': True})


@login_required
def property_detail(request, pk):
    prop = get_object_or_404(Property, pk=pk, owner=request.user)
    meters = prop.meters.select_related('service').all()
    txs = prop.transactions.all()[:10]
    return render(request, 'properties/detail.html', {
        'property': prop, 'meters': meters, 'txs': txs,
    })


@login_required
def property_edit(request, pk):
    prop = get_object_or_404(Property, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=prop)
        if form.is_valid():
            p = form.save(commit=False)
            if p.is_primary:
                Property.objects.filter(owner=request.user).exclude(pk=p.pk).update(is_primary=False)
            p.save()
            messages.success(request, 'Manzil yangilandi.')
            return redirect('property_detail', pk=p.pk)
    else:
        form = PropertyForm(instance=prop)
    return render(request, 'properties/form.html', {'form': form, 'is_new': False, 'property': prop})


@login_required
@require_POST
def property_delete(request, pk):
    prop = get_object_or_404(Property, pk=pk, owner=request.user)
    prop.delete()
    messages.success(request, 'Manzil o\'chirildi.')
    return redirect('properties_list')


@login_required
def meter_new(request, property_pk):
    prop = get_object_or_404(Property, pk=property_pk, owner=request.user)
    if request.method == 'POST':
        form = MeterForm(request.POST)
        if form.is_valid():
            m = form.save(commit=False)
            m.property = prop
            m.save()
            messages.success(request, 'Hisoblagich qo\'shildi.')
            return redirect('property_detail', pk=prop.pk)
    else:
        form = MeterForm()
    return render(request, 'meters/form.html', {'form': form, 'property': prop, 'is_new': True})


@login_required
def meter_reading_new(request, meter_pk):
    meter = get_object_or_404(Meter, pk=meter_pk, property__owner=request.user)
    last = meter.last_reading()
    prev_value = last.current_value if last else meter.initial_reading

    if request.method == 'POST':
        form = MeterReadingForm(request.POST, request.FILES)
        if form.is_valid():
            r = form.save(commit=False)
            r.meter = meter
            r.previous_value = prev_value
            r.save()
            anomalies = detect_anomalies_for_reading(r)
            if anomalies:
                messages.warning(request, f'Yozuv saqlandi, lekin {len(anomalies)} ta '
                                          f'anomaliya aniqlandi.')
            else:
                messages.success(request, f'Hisoblagich ko\'rsatkichi saqlandi: '
                                          f'sarf {r.consumption} {meter.service.unit}.')
            return redirect('meter_history', meter_pk=meter.pk)
    else:
        form = MeterReadingForm(initial={'previous_value': prev_value, 'reading_date': timezone.now().date()})
    return render(request, 'meters/reading_form.html', {
        'form': form, 'meter': meter, 'previous_value': prev_value,
    })


@login_required
def meter_history(request, meter_pk):
    meter = get_object_or_404(Meter, pk=meter_pk, property__owner=request.user)
    readings = meter.readings.all()

    # Chart uchun: 12 ta oxirgi yozuv
    chart_readings = list(readings.order_by('reading_date')[:24])
    chart_labels = [r.reading_date.strftime('%Y-%m-%d') for r in chart_readings]
    chart_data = [float(r.consumption) for r in chart_readings]

    return render(request, 'meters/history.html', {
        'meter': meter, 'readings': readings,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    })


# ============ PAYMENTS ============

@login_required
def payment_new(request, service_slug=None):
    initial_service = None
    if service_slug:
        try:
            initial_service = Service.objects.get(slug=service_slug)
        except Service.DoesNotExist:
            pass

    if request.method == 'POST':
        form = PaymentForm(request.user, request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            card = form.cleaned_data['card']

            # Mock to'lov bajarish
            tx = Transaction.objects.create(
                user=request.user,
                property=form.cleaned_data.get('property'),
                service=form.cleaned_data['service'],
                amount=amount,
                card=card,
                comment=form.cleaned_data.get('comment', ''),
                account_number=form.cleaned_data.get('account_number', ''),
                status='success',
            )

            # Karta balansidan yechish
            if card and card.balance >= amount:
                card.balance -= amount
                card.save()
            elif card:
                tx.status = 'failed'
                tx.comment = 'Kartada mablag\' yetarli emas'
                tx.save()
                messages.error(request, 'Kartada mablag\' yetarli emas.')
                return redirect('transaction_detail', pk=tx.pk)

            Notification.objects.create(
                user=request.user, type='payment', icon='bi-credit-card-fill',
                title='To\'lov muvaffaqiyatli',
                message=f'{tx.service.name} uchun {amount:,.0f} so\'m to\'landi.',
                link=f'/transactions/{tx.pk}/',
            )
            messages.success(request, f'To\'lov muvaffaqiyatli! Kvitansiya: {tx.receipt_number}')
            return redirect('transaction_detail', pk=tx.pk)
    else:
        initial = {}
        if initial_service:
            initial['service'] = initial_service
        primary_card = Card.objects.filter(user=request.user, is_primary=True).first()
        if primary_card:
            initial['card'] = primary_card
        form = PaymentForm(request.user, initial=initial)

    return render(request, 'payments/new.html', {
        'form': form, 'initial_service': initial_service,
    })


@login_required
def transactions_list(request):
    qs = Transaction.objects.filter(user=request.user).select_related('service', 'property')

    # Filtrlar
    q = request.GET.get('q', '').strip()
    service_id = request.GET.get('service')
    status_f = request.GET.get('status')
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')

    if q:
        qs = qs.filter(Q(comment__icontains=q) | Q(receipt_number__icontains=q) |
                       Q(service__name__icontains=q))
    if service_id:
        qs = qs.filter(service_id=service_id)
    if status_f:
        qs = qs.filter(status=status_f)
    if date_from:
        try:
            d = datetime.strptime(date_from, '%Y-%m-%d').date()
            qs = qs.filter(created_at__date__gte=d)
        except ValueError:
            pass
    if date_to:
        try:
            d = datetime.strptime(date_to, '%Y-%m-%d').date()
            qs = qs.filter(created_at__date__lte=d)
        except ValueError:
            pass

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page', 1))

    total = qs.aggregate(s=Sum('amount'))['s'] or 0

    return render(request, 'transactions/list.html', {
        'page': page, 'total_amount': total,
        'services': Service.objects.all(),
        'q': q, 'service_id': service_id, 'status_f': status_f,
        'date_from': date_from, 'date_to': date_to,
    })


@login_required
def transaction_detail(request, pk):
    tx = get_object_or_404(Transaction, pk=pk, user=request.user)
    return render(request, 'transactions/detail.html', {'tx': tx})


@login_required
def transactions_export_csv(request):
    qs = Transaction.objects.filter(user=request.user).select_related('service', 'property')
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="tranzaksiyalar.csv"'
    response.write('\ufeff')  # BOM for Excel
    writer = csv.writer(response)
    writer.writerow(['Sana', 'Kvitansiya', 'Xizmat', 'Manzil', 'Summa', 'Holat', 'Izoh'])
    for t in qs:
        writer.writerow([
            t.created_at.strftime('%Y-%m-%d %H:%M'), t.receipt_number,
            t.service.name if t.service else '', t.property.name if t.property else '',
            t.amount, t.get_status_display(), t.comment or '',
        ])
    return response


@login_required
def transaction_receipt(request, pk):
    tx = get_object_or_404(Transaction, pk=pk, user=request.user)
    return render(request, 'transactions/receipt.html', {'tx': tx})


# ============ CARDS ============

@login_required
def cards_list(request):
    cards = Card.objects.filter(user=request.user)
    return render(request, 'cards/list.html', {'cards': cards})


@login_required
def card_new(request):
    if request.method == 'POST':
        form = CardForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.user = request.user
            full = form.cleaned_data['full_number']
            c.number_last4 = full[-4:]
            if c.is_primary:
                Card.objects.filter(user=request.user).update(is_primary=False)
            c.save()
            messages.success(request, 'Karta qo\'shildi.')
            return redirect('cards_list')
    else:
        form = CardForm()
    return render(request, 'cards/form.html', {'form': form})


@login_required
@require_POST
def card_delete(request, pk):
    card = get_object_or_404(Card, pk=pk, user=request.user)
    card.delete()
    messages.success(request, 'Karta o\'chirildi.')
    return redirect('cards_list')


@login_required
@require_POST
def card_set_primary(request, pk):
    card = get_object_or_404(Card, pk=pk, user=request.user)
    Card.objects.filter(user=request.user).update(is_primary=False)
    card.is_primary = True
    card.save()
    messages.success(request, 'Asosiy karta o\'rnatildi.')
    return redirect('cards_list')


# ============ STATISTICS ============

@login_required
def statistics(request):
    user = request.user
    year = int(request.GET.get('year', timezone.now().year))
    available_years = list(range(timezone.now().year - 2, timezone.now().year + 1))

    monthly = monthly_consumption_chart(user, year=year)
    breakdown = current_month_breakdown(user)

    # Yillik sarf yig'indilari
    months = ['Yanv', 'Fev', 'Mart', 'Apr', 'May', 'Iyun',
              'Iyul', 'Avg', 'Sen', 'Okt', 'Noy', 'Dek']

    # Bar chart — bu oy vs o'tgan oy vs o'tgan yil shu oyi
    today = timezone.now().date()
    services = list(Service.objects.all())

    def _sum_for(year_val, month_val):
        result = {}
        for s in services:
            total = MeterReading.objects.filter(
                meter__property__owner=user, meter__service=s,
                reading_date__year=year_val, reading_date__month=month_val,
            ).aggregate(c=Sum('consumption'))['c'] or 0
            result[s.name] = float(total)
        return result

    cur = _sum_for(today.year, today.month)
    prev_month = today.replace(day=1) - timedelta(days=1)
    pm = _sum_for(prev_month.year, prev_month.month)
    py = _sum_for(today.year - 1, today.month)

    bar_labels = [s.name for s in services]
    bar_current = [cur[n] for n in bar_labels]
    bar_prev_month = [pm[n] for n in bar_labels]
    bar_prev_year = [py[n] for n in bar_labels]

    # Yillik xulosa
    year_total = Transaction.objects.filter(
        user=user, status='success', created_at__year=year,
    ).aggregate(s=Sum('amount'))['s'] or 0

    monthly_totals = []
    for m in range(1, 13):
        t = Transaction.objects.filter(
            user=user, status='success',
            created_at__year=year, created_at__month=m,
        ).aggregate(s=Sum('amount'))['s'] or 0
        monthly_totals.append(float(t))

    most_expensive = max(range(12), key=lambda i: monthly_totals[i]) if monthly_totals else 0
    cheapest = min(
        [i for i, v in enumerate(monthly_totals) if v > 0],
        key=lambda i: monthly_totals[i], default=0
    )

    return render(request, 'statistics.html', {
        'year': year, 'available_years': available_years,
        'months': months,
        'monthly_data_json': json.dumps(monthly),
        'breakdown_json': json.dumps([
            {'name': k, 'amount': v['amount'], 'color': v['color']}
            for k, v in breakdown.items()
        ]),
        'bar_labels_json': json.dumps(bar_labels),
        'bar_current_json': json.dumps(bar_current),
        'bar_prev_month_json': json.dumps(bar_prev_month),
        'bar_prev_year_json': json.dumps(bar_prev_year),
        'year_total': year_total,
        'monthly_totals_json': json.dumps(monthly_totals),
        'most_expensive_month': months[most_expensive],
        'most_expensive_amount': monthly_totals[most_expensive] if monthly_totals else 0,
        'cheapest_month': months[cheapest],
        'cheapest_amount': monthly_totals[cheapest] if monthly_totals else 0,
        # Hududiy o'rtacha (mock)
        'region_average_diff': -20,  # 20% kam
    })


# ============ ANOMALIES ============

@login_required
def anomalies_list(request):
    show = request.GET.get('show', 'open')
    qs = Anomaly.objects.filter(user=request.user)
    if show == 'open':
        qs = qs.filter(is_resolved=False)
    elif show == 'resolved':
        qs = qs.filter(is_resolved=True)
    return render(request, 'anomalies/list.html', {'anomalies': qs, 'show': show})


@login_required
@require_POST
def anomaly_resolve(request, pk):
    a = get_object_or_404(Anomaly, pk=pk, user=request.user)
    a.is_resolved = True
    a.save()
    messages.success(request, 'Anomaliya hal qilindi deb belgilandi.')
    return redirect('anomalies_list')


# ============ NOTIFICATIONS ============

@login_required
def notifications_list(request):
    notifs = Notification.objects.filter(user=request.user)
    return render(request, 'notifications/list.html', {'notifications': notifs})


@login_required
@require_POST
def notification_read(request, pk):
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    n.is_read = True
    n.save()
    if n.link:
        return redirect(n.link)
    return redirect('notifications_list')


@login_required
@require_POST
def notifications_read_all(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'Barchasi o\'qilgan deb belgilandi.')
    return redirect('notifications_list')


@login_required
@require_POST
def notification_delete(request, pk):
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    n.delete()
    return redirect('notifications_list')


# ============ REMINDERS ============

@login_required
def reminders_list(request):
    rs = Reminder.objects.filter(user=request.user).select_related('service', 'property')
    return render(request, 'reminders/list.html', {'reminders': rs})


@login_required
def reminder_new(request):
    if request.method == 'POST':
        form = ReminderForm(request.user, request.POST)
        if form.is_valid():
            r = form.save(commit=False)
            r.user = request.user
            r.save()
            messages.success(request, 'Eslatma qo\'shildi.')
            return redirect('reminders_list')
    else:
        form = ReminderForm(request.user)
    return render(request, 'reminders/form.html', {'form': form})


@login_required
@require_POST
def reminder_delete(request, pk):
    r = get_object_or_404(Reminder, pk=pk, user=request.user)
    r.delete()
    return redirect('reminders_list')


# ============ AUTO PAYMENTS ============

@login_required
def auto_payments_list(request):
    items = AutoPayment.objects.filter(user=request.user).select_related('service', 'property', 'card')
    return render(request, 'auto_payments/list.html', {'items': items})


@login_required
def auto_payment_new(request):
    if request.method == 'POST':
        form = AutoPaymentForm(request.user, request.POST)
        if form.is_valid():
            ap = form.save(commit=False)
            ap.user = request.user
            ap.save()
            messages.success(request, 'Avtomatik to\'lov qo\'shildi.')
            return redirect('auto_payments_list')
    else:
        form = AutoPaymentForm(request.user)
    return render(request, 'auto_payments/form.html', {'form': form})


@login_required
@require_POST
def auto_payment_delete(request, pk):
    ap = get_object_or_404(AutoPayment, pk=pk, user=request.user)
    ap.delete()
    return redirect('auto_payments_list')


# ============ REPORTS ============

@login_required
def reports(request):
    user = request.user
    year = int(request.GET.get('year', timezone.now().year))
    available_years = list(range(timezone.now().year - 2, timezone.now().year + 1))
    properties = Property.objects.filter(owner=user)

    # Yillik hisobot
    year_total = Transaction.objects.filter(
        user=user, status='success', created_at__year=year,
    ).aggregate(s=Sum('amount'))['s'] or 0

    by_service = Transaction.objects.filter(
        user=user, status='success', created_at__year=year,
    ).values('service__name', 'service__icon', 'service__color').annotate(
        total=Sum('amount'), count=Count('id'),
    ).order_by('-total')

    by_property = Transaction.objects.filter(
        user=user, status='success', created_at__year=year,
    ).values('property__name').annotate(
        total=Sum('amount'), count=Count('id'),
    ).order_by('-total')

    return render(request, 'reports.html', {
        'year': year, 'available_years': available_years,
        'year_total': year_total,
        'by_service': by_service, 'by_property': by_property,
        'properties': properties,
    })


# ============ FAMILY ============

@login_required
def family_list(request):
    invites = FamilyMember.objects.filter(owner=request.user).select_related('member', 'property')
    member_in = FamilyMember.objects.filter(member=request.user).select_related('owner', 'property')

    if request.method == 'POST':
        form = FamilyInviteForm(request.user, request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            user = User.objects.get(phone=phone)
            FamilyMember.objects.update_or_create(
                owner=request.user, member=user,
                property=form.cleaned_data['property'],
                defaults={'role': form.cleaned_data['role']},
            )
            Notification.objects.create(
                user=user, type='system', icon='bi-people-fill',
                title='Sizni oilaga taklif qilishdi',
                message=f'{request.user.display_name} sizni "{form.cleaned_data["property"].name}" '
                        f'manziliga a\'zo qilib qo\'shdi.',
            )
            messages.success(request, f'{user.display_name} oilaga qo\'shildi.')
            return redirect('family_list')
    else:
        form = FamilyInviteForm(request.user)

    return render(request, 'family/list.html', {
        'invites': invites, 'member_in': member_in, 'form': form,
    })


@login_required
@require_POST
def family_remove(request, pk):
    fm = get_object_or_404(FamilyMember, pk=pk, owner=request.user)
    fm.delete()
    messages.success(request, 'A\'zo o\'chirildi.')
    return redirect('family_list')


# ============ TARIFFS ============

@login_required
def tariffs_list(request):
    region = request.GET.get('region', request.user.region or 'Toshkent')
    tariffs = Tariff.objects.filter(is_active=True).select_related('service').order_by(
        'service__name', '-valid_from')
    if region:
        tariffs = tariffs.filter(region=region)
    return render(request, 'tariffs.html', {'tariffs': tariffs, 'region': region})


# ============ SETTINGS / PROFILE ============

@login_required
def profile(request):
    return render(request, 'profile.html', {'user': request.user})


@login_required
def settings_view(request):
    form = ProfileForm(instance=request.user)
    pwd_form = ChangePasswordForm(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'profile':
            form = ProfileForm(request.POST, request.FILES, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profil yangilandi.')
                return redirect('settings')
        elif action == 'password':
            pwd_form = ChangePasswordForm(user=request.user, data=request.POST)
            if pwd_form.is_valid():
                request.user.set_password(pwd_form.cleaned_data['new_password'])
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Parol o\'zgartirildi.')
                return redirect('settings')
        elif action == 'delete_account':
            request.user.delete()
            messages.info(request, 'Hisob o\'chirildi.')
            return redirect('landing')
        elif action == 'topup':
            try:
                amt = Decimal(request.POST.get('amount', '0'))
                if amt > 0:
                    request.user.balance += amt
                    request.user.save()
                    messages.success(request, f'Balans {amt:,.0f} so\'mga to\'ldirildi.')
            except Exception:
                messages.error(request, 'Summa noto\'g\'ri.')
            return redirect('dashboard')

    return render(request, 'settings.html', {
        'form': form, 'pwd_form': pwd_form,
    })


# ============ TOP UP BALANCE ============

@login_required
def topup(request):
    if request.method == 'POST':
        try:
            amt = Decimal(request.POST.get('amount', '0'))
            card_id = request.POST.get('card')
            if amt <= 0:
                raise ValueError
            card = Card.objects.filter(pk=card_id, user=request.user).first() if card_id else None
            if card:
                if card.balance < amt:
                    messages.error(request, 'Kartada mablag\' yetarli emas.')
                    return redirect('topup')
                card.balance -= amt
                card.save()
            request.user.balance += amt
            request.user.save()
            Transaction.objects.create(
                user=request.user, amount=amt, card=card, status='success',
                comment='Hisobni to\'ldirish',
            )
            Notification.objects.create(
                user=request.user, type='payment', icon='bi-wallet2',
                title='Balans to\'ldirildi',
                message=f'Hisobingiz {amt:,.0f} so\'mga to\'ldirildi.',
            )
            messages.success(request, f'Balans {amt:,.0f} so\'mga to\'ldirildi.')
            return redirect('dashboard')
        except Exception:
            messages.error(request, 'Summa noto\'g\'ri.')

    cards = Card.objects.filter(user=request.user, is_active=True)
    return render(request, 'topup.html', {'cards': cards})
