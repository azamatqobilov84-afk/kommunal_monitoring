"""
Formalar — ro'yxat, kirish, manzillar, hisoblagichlar va h.k.
"""
import re
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import (
    User, Property, Meter, MeterReading, Card, Transaction,
    Reminder, AutoPayment, Notification, Service,
)


PHONE_REGEX = re.compile(r'^\+?998\d{9}$')


def normalize_phone(value):
    v = re.sub(r'[\s\-\(\)]', '', value or '')
    if v and not v.startswith('+'):
        if v.startswith('998'):
            v = '+' + v
        elif v.startswith('9'):
            v = '+998' + v[1:] if v.startswith('98') else '+998' + v
    return v


class PhoneRegisterForm(forms.Form):
    """1-bosqich: telefon raqam kiritish va SMS yuborish."""
    phone = forms.CharField(label='Telefon raqami', max_length=20,
                            widget=forms.TextInput(attrs={
                                'placeholder': '+998 90 123 45 67',
                                'class': 'form-control form-control-lg',
                            }))

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data['phone'])
        if not PHONE_REGEX.match(phone):
            raise ValidationError('Telefon raqami noto\'g\'ri formatda. Masalan: +998901234567')
        if User.objects.filter(phone=phone).exists():
            raise ValidationError('Bu raqam bilan foydalanuvchi mavjud. Kirishni urinib ko\'ring.')
        return phone


class SmsConfirmForm(forms.Form):
    """2-bosqich: SMS kodini tasdiqlash + parol o'rnatish."""
    code = forms.CharField(label='SMS kod', max_length=6, widget=forms.TextInput(attrs={
        'placeholder': '6 xonali kod', 'class': 'form-control form-control-lg text-center',
        'autocomplete': 'one-time-code',
    }))
    first_name = forms.CharField(label='Ism', max_length=50, widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg', 'placeholder': 'Ismingiz'
    }))
    last_name = forms.CharField(label='Familiya', max_length=50, widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg', 'placeholder': 'Familiyangiz'
    }))
    password = forms.CharField(label='Parol', widget=forms.PasswordInput(attrs={
        'class': 'form-control form-control-lg', 'placeholder': 'Kamida 4 belgi'
    }))

    def clean_password(self):
        p = self.cleaned_data['password']
        if len(p) < 4:
            raise ValidationError('Parol kamida 4 belgidan iborat bo\'lishi kerak.')
        return p


class LoginForm(forms.Form):
    phone = forms.CharField(label='Telefon', widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg', 'placeholder': '+998901234567',
        'autocomplete': 'tel',
    }))
    password = forms.CharField(label='Parol', widget=forms.PasswordInput(attrs={
        'class': 'form-control form-control-lg', 'placeholder': 'Parol',
        'autocomplete': 'current-password',
    }))

    def clean_phone(self):
        return normalize_phone(self.cleaned_data['phone'])


class PasswordResetPhoneForm(forms.Form):
    phone = forms.CharField(label='Telefon', widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg',
    }))

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data['phone'])
        if not User.objects.filter(phone=phone).exists():
            raise ValidationError('Bu raqam bilan foydalanuvchi topilmadi.')
        return phone


class PasswordResetConfirmForm(forms.Form):
    code = forms.CharField(label='SMS kod', max_length=6, widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg text-center',
    }))
    new_password = forms.CharField(label='Yangi parol', widget=forms.PasswordInput(attrs={
        'class': 'form-control form-control-lg',
    }))


from .locations import REGION_CHOICES, UZBEKISTAN_LOCATIONS


class PropertyForm(forms.ModelForm):
    region = forms.ChoiceField(
        label='Viloyat',
        choices=[('', '— Viloyatni tanlang —')] + REGION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'id_region'}),
    )
    district = forms.ChoiceField(
        label='Tuman / Shahar',
        choices=[('', '— Avval viloyatni tanlang —')],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'id_district'}),
    )

    class Meta:
        model = Property
        fields = ['name', 'region', 'district', 'mahalla', 'street',
                  'house_number', 'apartment', 'rooms', 'area_sqm', 'is_primary']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-lg',
                                            'placeholder': 'Masalan: Asosiy uy'}),
            'mahalla': forms.TextInput(attrs={'class': 'form-control',
                                               'placeholder': 'Masalan: Bunyodkor MFY'}),
            'street': forms.TextInput(attrs={'class': 'form-control',
                                              'placeholder': "Masalan: Amir Temur"}),
            'house_number': forms.TextInput(attrs={'class': 'form-control',
                                                   'placeholder': '23'}),
            'apartment': forms.TextInput(attrs={'class': 'form-control',
                                                'placeholder': '45 (ixtiyoriy)'}),
            'rooms': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 20}),
            'area_sqm': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # District choicesni dinamik to'ldirish — instance yoki POST data bo'lsa
        region = None
        if self.is_bound:
            region = self.data.get('region')
        elif self.instance and self.instance.pk:
            region = self.instance.region
        if region and region in UZBEKISTAN_LOCATIONS:
            districts = UZBEKISTAN_LOCATIONS[region]
            self.fields['district'].choices = (
                [('', '— Tumanni tanlang —')] + [(d, d) for d in districts]
            )

    def clean(self):
        cleaned = super().clean()
        region = cleaned.get('region')
        district = cleaned.get('district')
        if region and district:
            if district not in UZBEKISTAN_LOCATIONS.get(region, []):
                self.add_error('district',
                               f'"{district}" "{region}" viloyatiga tegishli emas.')
        return cleaned


class MeterForm(forms.ModelForm):
    class Meta:
        model = Meter
        fields = ['service', 'serial_number', 'installed_at', 'tariff_mode',
                  'initial_reading', 'account_number']
        widgets = {
            'service': forms.Select(attrs={'class': 'form-select'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'installed_at': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tariff_mode': forms.Select(attrs={'class': 'form-select'}),
            'initial_reading': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class MeterReadingForm(forms.ModelForm):
    class Meta:
        model = MeterReading
        fields = ['previous_value', 'current_value', 'reading_date', 'image', 'note']
        widgets = {
            'previous_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01',
                                                       'readonly': 'readonly'}),
            'current_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01',
                                                       'autofocus': 'autofocus'}),
            'reading_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'note': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        prev = cleaned.get('previous_value')
        curr = cleaned.get('current_value')
        if prev is not None and curr is not None and curr < prev:
            self.add_error('current_value',
                           'Joriy ko\'rsatkich avvalgidan kichik bo\'lishi mumkin emas.')
        return cleaned


class CardForm(forms.ModelForm):
    full_number = forms.CharField(label='Karta raqami', max_length=19, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': '8600 0000 0000 0000', 'inputmode': 'numeric',
    }))

    class Meta:
        model = Card
        fields = ['card_type', 'holder_name', 'expiry_month', 'expiry_year', 'is_primary']
        widgets = {
            'card_type': forms.Select(attrs={'class': 'form-select'}),
            'holder_name': forms.TextInput(attrs={'class': 'form-control',
                                                  'placeholder': 'AKMAL KARIMOV'}),
            'expiry_month': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12,
                                                     'placeholder': 'MM'}),
            'expiry_year': forms.NumberInput(attrs={'class': 'form-control', 'min': 2025,
                                                    'max': 2040, 'placeholder': 'YYYY'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_full_number(self):
        n = re.sub(r'\s+', '', self.cleaned_data['full_number'])
        if not n.isdigit() or len(n) != 16:
            raise ValidationError('Karta raqami 16 raqamdan iborat bo\'lishi kerak.')
        return n


class PaymentForm(forms.Form):
    """Mock to'lov formasi."""
    service = forms.ModelChoiceField(label='Xizmat', queryset=Service.objects.all(),
                                     widget=forms.Select(attrs={'class': 'form-select'}))
    property = forms.ModelChoiceField(label='Manzil', queryset=Property.objects.none(),
                                      widget=forms.Select(attrs={'class': 'form-select'}),
                                      required=False)
    amount = forms.DecimalField(label='Summa (so\'m)', max_digits=12, decimal_places=2,
                                widget=forms.NumberInput(attrs={
                                    'class': 'form-control form-control-lg',
                                    'placeholder': '0', 'step': '1000',
                                }))
    card = forms.ModelChoiceField(label='Karta', queryset=Card.objects.none(),
                                  widget=forms.Select(attrs={'class': 'form-select'}))
    account_number = forms.CharField(label='Shaxsiy hisob raqami', max_length=30, required=False,
                                     widget=forms.TextInput(attrs={'class': 'form-control'}))
    comment = forms.CharField(label='Izoh', max_length=255, required=False,
                              widget=forms.TextInput(attrs={'class': 'form-control'}))

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['property'].queryset = Property.objects.filter(owner=user)
            self.fields['card'].queryset = Card.objects.filter(user=user, is_active=True)


class ReminderForm(forms.ModelForm):
    class Meta:
        model = Reminder
        fields = ['service', 'property', 'day_of_month', 'message', 'is_active']
        widgets = {
            'service': forms.Select(attrs={'class': 'form-select'}),
            'property': forms.Select(attrs={'class': 'form-select'}),
            'day_of_month': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 28}),
            'message': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['property'].queryset = Property.objects.filter(owner=user)


class AutoPaymentForm(forms.ModelForm):
    class Meta:
        model = AutoPayment
        fields = ['service', 'property', 'card', 'day_of_month', 'max_amount', 'is_active']
        widgets = {
            'service': forms.Select(attrs={'class': 'form-select'}),
            'property': forms.Select(attrs={'class': 'form-select'}),
            'card': forms.Select(attrs={'class': 'form-select'}),
            'day_of_month': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 28}),
            'max_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '1000'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['property'].queryset = Property.objects.filter(owner=user)
            self.fields['card'].queryset = Card.objects.filter(user=user, is_active=True)


class ProfileForm(forms.ModelForm):
    region = forms.ChoiceField(
        label='Viloyat',
        choices=[('', '— Viloyatni tanlang —')] + REGION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'address',
                  'region', 'avatar', 'language', 'notify_threshold_percent']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'notify_threshold_percent': forms.NumberInput(attrs={'class': 'form-control',
                                                                  'min': 5, 'max': 200}),
        }


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(label='Joriy parol', widget=forms.PasswordInput(attrs={
        'class': 'form-control'
    }))
    new_password = forms.CharField(label='Yangi parol', widget=forms.PasswordInput(attrs={
        'class': 'form-control'
    }))
    new_password2 = forms.CharField(label='Yangi parolni takrorlang', widget=forms.PasswordInput(attrs={
        'class': 'form-control'
    }))

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_old_password(self):
        op = self.cleaned_data['old_password']
        if not self.user.check_password(op):
            raise ValidationError('Joriy parol noto\'g\'ri.')
        return op

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password')
        p2 = cleaned.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError('Parollar mos kelmadi.')
        if p1 and len(p1) < 4:
            raise ValidationError('Parol kamida 4 belgidan iborat bo\'lishi kerak.')
        return cleaned


class FamilyInviteForm(forms.Form):
    phone = forms.CharField(label='A\'zoning telefoni', widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': '+998901234567',
    }))
    property = forms.ModelChoiceField(label='Manzil', queryset=Property.objects.none(),
                                      widget=forms.Select(attrs={'class': 'form-select'}))
    role = forms.ChoiceField(label='Rol', choices=[
        ('viewer', 'Faqat ko\'rish'), ('editor', 'Tahrirlash'),
    ], widget=forms.Select(attrs={'class': 'form-select'}))

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['property'].queryset = Property.objects.filter(owner=user)
            self._user = user

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data['phone'])
        try:
            u = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise ValidationError('Bu raqam bilan foydalanuvchi topilmadi. '
                                  'A\'zo avval ro\'yxatdan o\'tishi kerak.')
        if u == self._user:
            raise ValidationError('O\'zingizni a\'zo qilib qo\'sha olmaysiz.')
        return phone
