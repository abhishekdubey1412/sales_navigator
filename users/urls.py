from django.urls import path
from . import views

urlpatterns = [
    path('overview/', views.overview, name='overview'),
    path('settings/', views.settings, name='settings'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('update-email/', views.update_email, name='update_email'),
    path('change-password/', views.change_password, name='change_password'),
    path('billing/', views.billing, name='billing'),
    path('statements/', views.statements, name='statements'),
    path('api-keys/', views.api_keys, name='api_keys'),
    path('logs/', views.logs, name='logs'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('users-list/', views.users_list, name='users_list'),
    path('add-user/', views.add_user, name='add_user'),
    path('update-role/', views.update_role, name='update_role'),
    path('user-activate/<int:user_id>/', views.user_activate, name='user_activate'),
    path('user-deactivate/<int:user_id>/', views.user_deactivate, name='user_deactivate'),
    path('roles/', views.roles, name='roles'),
    path('user-role/', views.user_role, name='user_role'),
    path('scrape-content/', views.scrape_content, name='scrape_content'),
    path('customization/', views.customization, name='customization'),
]