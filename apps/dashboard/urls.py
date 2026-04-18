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
    path('members/export/', views.members_export, name='members_export'),
    path('members/import/', views.members_import, name='members_import'),
    path('members/download-template/', views.members_download_template, name='members_download_template'),
    path('members/<uuid:member_id>/', views.member_detail, name='member_detail'),
    path('members/<uuid:member_id>/edit/', views.member_edit, name='member_edit'),
    path('members/<uuid:member_id>/add-to-ministry/', views.member_add_to_ministry, name='member_add_to_ministry'),
    path('members/<uuid:member_id>/add-to-family/', views.member_add_to_family, name='member_add_to_family'),
    
    # Ministries
    path('ministries/', views.ministries_list, name='ministries_list'),
    path('ministries/create/', views.ministry_create, name='ministry_create'),
    path('ministries/export/', views.ministries_export, name='ministries_export'),
    path('ministries/import/', views.ministries_import, name='ministries_import'),
    path('ministries/download-template/', views.ministries_download_template, name='ministries_download_template'),
    path('ministries/<uuid:ministry_id>/', views.ministry_detail, name='ministry_detail'),
    path('ministries/<uuid:ministry_id>/edit/', views.ministry_edit, name='ministry_edit'),
    path('ministries/<uuid:ministry_id>/add-member/', views.ministry_add_member, name='ministry_add_member'),
    path('ministries/<uuid:ministry_id>/remove-member/<uuid:member_ministry_id>/', views.ministry_remove_member, name='ministry_remove_member'),
    
    # Families
    path('families/', views.families_list, name='families_list'),
    path('families/create/', views.family_create, name='family_create'),
    path('families/export/', views.families_export, name='families_export'),
    path('families/import/', views.families_import, name='families_import'),
    path('families/download-template/', views.families_download_template, name='families_download_template'),
    path('families/<uuid:family_id>/', views.family_detail, name='family_detail'),
    path('families/<uuid:family_id>/edit/', views.family_edit, name='family_edit'),
    path('families/<uuid:family_id>/add-member/', views.family_add_member, name='family_add_member'),
    path('families/<uuid:family_id>/remove-member/<uuid:family_member_id>/', views.family_remove_member, name='family_remove_member'),
    
    # Events
    path('events/', views.events_list, name='events_list'),
    path('events/create/', views.event_create, name='event_create'),
    path('events/export/', views.events_export, name='events_export'),
    path('events/import/', views.events_import, name='events_import'),
    path('events/download-template/', views.events_download_template, name='events_download_template'),
    path('events/<uuid:event_id>/', views.event_detail, name='event_detail'),
    path('events/<uuid:event_id>/edit/', views.event_edit, name='event_edit'),
    path('events/<uuid:event_id>/add-work-group/', views.event_add_work_group, name='event_add_work_group'),
    path('events/<uuid:event_id>/remove-work-group/<uuid:work_group_id>/', views.event_remove_work_group, name='event_remove_work_group'),
    path('events/<uuid:event_id>/work-group/<uuid:work_group_id>/add-worker/', views.event_add_worker, name='event_add_worker'),
    path('events/<uuid:event_id>/work-group/<uuid:work_group_id>/remove-worker/<uuid:worker_id>/', views.event_remove_worker, name='event_remove_worker'),
    
    # Event Budget
    path('events/<uuid:event_id>/update-budget/', views.event_update_budget, name='event_update_budget'),
    path('events/<uuid:event_id>/add-income/', views.event_add_income, name='event_add_income'),
    path('events/<uuid:event_id>/remove-income/<uuid:income_id>/', views.event_remove_income, name='event_remove_income'),
    path('events/<uuid:event_id>/add-expense/', views.event_add_expense, name='event_add_expense'),
    path('events/<uuid:event_id>/remove-expense/<uuid:expense_id>/', views.event_remove_expense, name='event_remove_expense'),

    # Event Lodging
    path('events/<uuid:event_id>/lodging/', views.event_lodging, name='event_lodging'),
    path('events/<uuid:event_id>/lodging/add-host/', views.event_lodging_add_host, name='event_lodging_add_host'),
    path('events/<uuid:event_id>/lodging/remove-host/<uuid:host_id>/', views.event_lodging_remove_host, name='event_lodging_remove_host'),
    path('events/<uuid:event_id>/lodging/host/<uuid:host_id>/add-guest/', views.event_lodging_add_guest, name='event_lodging_add_guest'),
    path('events/<uuid:event_id>/lodging/remove-guest/<uuid:guest_id>/', views.event_lodging_remove_guest, name='event_lodging_remove_guest'),
]
