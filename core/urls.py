"""
URL marshrutlari.
"""
from django.urls import path

from . import views

urlpatterns = [
    # Landing & auth
    path('', views.landing, name='landing'),
    path('register/', views.register_phone, name='register'),
    path('register/confirm/', views.register_confirm, name='register_confirm'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset, name='password_reset'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),

    # API
    path('api/districts/', views.api_districts, name='api_districts'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('topup/', views.topup, name='topup'),

    # Properties
    path('properties/', views.properties_list, name='properties_list'),
    path('properties/new/', views.property_new, name='property_new'),
    path('properties/<int:pk>/', views.property_detail, name='property_detail'),
    path('properties/<int:pk>/edit/', views.property_edit, name='property_edit'),
    path('properties/<int:pk>/delete/', views.property_delete, name='property_delete'),

    # Meters
    path('properties/<int:property_pk>/meters/new/', views.meter_new, name='meter_new'),
    path('meters/<int:meter_pk>/reading/new/', views.meter_reading_new, name='meter_reading_new'),
    path('meters/<int:meter_pk>/history/', views.meter_history, name='meter_history'),

    # Payments
    path('payments/new/', views.payment_new, name='payment_new'),
    path('payments/<slug:service_slug>/', views.payment_new, name='payment_service'),

    # Transactions
    path('transactions/', views.transactions_list, name='transactions_list'),
    path('transactions/export/', views.transactions_export_csv, name='transactions_export'),
    path('transactions/<int:pk>/', views.transaction_detail, name='transaction_detail'),
    path('transactions/<int:pk>/receipt/', views.transaction_receipt, name='transaction_receipt'),

    # Cards
    path('cards/', views.cards_list, name='cards_list'),
    path('cards/new/', views.card_new, name='card_new'),
    path('cards/<int:pk>/delete/', views.card_delete, name='card_delete'),
    path('cards/<int:pk>/primary/', views.card_set_primary, name='card_set_primary'),

    # Statistics & reports
    path('statistics/', views.statistics, name='statistics'),
    path('reports/', views.reports, name='reports'),

    # Anomalies
    path('anomalies/', views.anomalies_list, name='anomalies_list'),
    path('anomalies/<int:pk>/resolve/', views.anomaly_resolve, name='anomaly_resolve'),

    # Notifications
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:pk>/read/', views.notification_read, name='notification_read'),
    path('notifications/read-all/', views.notifications_read_all, name='notifications_read_all'),
    path('notifications/<int:pk>/delete/', views.notification_delete, name='notification_delete'),

    # Reminders
    path('reminders/', views.reminders_list, name='reminders_list'),
    path('reminders/new/', views.reminder_new, name='reminder_new'),
    path('reminders/<int:pk>/delete/', views.reminder_delete, name='reminder_delete'),

    # Auto payments
    path('auto-payments/', views.auto_payments_list, name='auto_payments_list'),
    path('auto-payments/new/', views.auto_payment_new, name='auto_payment_new'),
    path('auto-payments/<int:pk>/delete/', views.auto_payment_delete, name='auto_payment_delete'),

    # Family
    path('family/', views.family_list, name='family_list'),
    path('family/<int:pk>/remove/', views.family_remove, name='family_remove'),

    # Tariffs
    path('tariffs/', views.tariffs_list, name='tariffs_list'),

    # Settings
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings_view, name='settings'),
]
