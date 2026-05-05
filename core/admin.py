"""
Django admin paneli sozlamalari.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    User, Property, Service, Tariff, Meter, MeterReading,
    Card, Transaction, Notification, Reminder, AutoPayment,
    Anomaly, FamilyMember, SmsCode,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('phone', 'first_name', 'last_name', 'balance', 'is_staff')
    search_fields = ('phone', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Shaxsiy', {'fields': ('first_name', 'last_name', 'email', 'phone',
                                  'address', 'region', 'avatar', 'language')}),
        ('Hisob', {'fields': ('balance', 'pin_code', 'notify_threshold_percent')}),
        ('Ruxsatlar', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups',
                                   'user_permissions')}),
        ('Sanalar', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',),
                'fields': ('username', 'phone', 'first_name', 'last_name',
                           'password1', 'password2')}),
    )


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'region', 'district', 'mahalla', 'is_primary')
    list_filter = ('region', 'is_primary')
    search_fields = ('name', 'address', 'owner__phone', 'mahalla', 'street')
    fieldsets = (
        (None, {'fields': ('owner', 'name', 'is_primary')}),
        ('Manzil', {'fields': ('region', 'district', 'mahalla',
                                'street', 'house_number', 'apartment', 'address')}),
        ('Uy ma\'lumotlari', {'fields': ('rooms', 'area_sqm')}),
    )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'unit', 'has_meter')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ('service', 'tariff_type', 'region', 'price_per_unit', 'valid_from', 'is_active')
    list_filter = ('service', 'tariff_type', 'region', 'is_active')


@admin.register(Meter)
class MeterAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'service', 'property', 'tariff_mode', 'is_active')
    list_filter = ('service', 'tariff_mode', 'is_active')
    search_fields = ('serial_number', 'account_number')


@admin.register(MeterReading)
class MeterReadingAdmin(admin.ModelAdmin):
    list_display = ('meter', 'reading_date', 'previous_value', 'current_value',
                    'consumption', 'is_anomaly')
    list_filter = ('is_anomaly', 'reading_date', 'meter__service')
    date_hierarchy = 'reading_date'


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('user', 'card_type', 'masked_number', 'holder_name',
                    'balance', 'is_primary', 'is_active')
    list_filter = ('card_type', 'is_primary', 'is_active')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'user', 'service', 'amount', 'status', 'created_at')
    list_filter = ('status', 'service', 'is_auto')
    search_fields = ('receipt_number', 'user__phone', 'comment')
    date_hierarchy = 'created_at'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read')


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'day_of_month', 'is_active')


@admin.register(AutoPayment)
class AutoPaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'property', 'day_of_month', 'max_amount', 'is_active')


@admin.register(Anomaly)
class AnomalyAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'severity', 'is_resolved', 'detected_at')
    list_filter = ('severity', 'is_resolved')
    actions = ['mark_resolved']

    def mark_resolved(self, request, queryset):
        queryset.update(is_resolved=True)
    mark_resolved.short_description = 'Hal qilingan deb belgilash'


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ('owner', 'member', 'property', 'role')


@admin.register(SmsCode)
class SmsCodeAdmin(admin.ModelAdmin):
    list_display = ('phone', 'code', 'purpose', 'is_used', 'created_at')
    list_filter = ('purpose', 'is_used')


admin.site.site_header = 'Kommunal monitoringi — Admin panel'
admin.site.site_title = 'Kommunal monitoringi'
admin.site.index_title = 'Tizim boshqaruvi'
