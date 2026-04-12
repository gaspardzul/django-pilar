from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('settings/generate-api-key/', views.generate_api_key, name='generate_api_key'),
    path('subscription/plans/', views.subscription_plans, name='subscription_plans'),
    path('subscription/plans/<slug:plan_slug>/subscribe/', views.subscribe_to_plan, name='subscribe_to_plan'),
    path('subscription/cancel/', views.cancel_subscription, name='cancel_subscription'),
    path('subscription/trial/', views.start_trial, name='start_trial'),
    
    # Members
    path('members/', views.members_list, name='members_list'),
    path('members/create/', views.member_create, name='member_create'),
    path('members/<uuid:member_id>/', views.member_detail, name='member_detail'),
    path('members/<uuid:member_id>/edit/', views.member_edit, name='member_edit'),
    path('members/<uuid:member_id>/add-to-ministry/', views.member_add_to_ministry, name='member_add_to_ministry'),
    path('members/<uuid:member_id>/add-to-family/', views.member_add_to_family, name='member_add_to_family'),
    
    # Ministries
    path('ministries/', views.ministries_list, name='ministries_list'),
    path('ministries/create/', views.ministry_create, name='ministry_create'),
    path('ministries/<uuid:ministry_id>/', views.ministry_detail, name='ministry_detail'),
    path('ministries/<uuid:ministry_id>/edit/', views.ministry_edit, name='ministry_edit'),
    path('ministries/<uuid:ministry_id>/add-member/', views.ministry_add_member, name='ministry_add_member'),
    path('ministries/<uuid:ministry_id>/remove-member/<uuid:member_ministry_id>/', views.ministry_remove_member, name='ministry_remove_member'),
    
    # Families
    path('families/', views.families_list, name='families_list'),
    path('families/create/', views.family_create, name='family_create'),
    path('families/<uuid:family_id>/', views.family_detail, name='family_detail'),
    path('families/<uuid:family_id>/edit/', views.family_edit, name='family_edit'),
    path('families/<uuid:family_id>/add-member/', views.family_add_member, name='family_add_member'),
    path('families/<uuid:family_id>/remove-member/<uuid:family_member_id>/', views.family_remove_member, name='family_remove_member'),
]
