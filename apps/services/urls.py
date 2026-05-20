from django.urls import path

from . import views

app_name = 'services'

urlpatterns = [
    # Calendario mensual
    path('', views.calendar_view, name='calendar'),

    # Tipos de servicio
    path('types/', views.service_types_list, name='types_list'),
    path('types/create/', views.service_type_create, name='type_create'),
    path('types/<uuid:type_id>/edit/', views.service_type_edit, name='type_edit'),
    path('types/<uuid:type_id>/parts/', views.service_type_parts, name='type_parts'),
    path('types/<uuid:type_id>/parts/create/', views.service_part_create, name='part_create'),
    path('types/<uuid:type_id>/parts/<uuid:part_id>/edit/', views.service_part_edit, name='part_edit'),
    path('types/<uuid:type_id>/parts/<uuid:part_id>/eligible/', views.part_eligible_members, name='part_eligible'),
    path('types/<uuid:type_id>/parts/<uuid:part_id>/eligible/toggle/', views.part_toggle_eligible, name='part_toggle_eligible'),

    # Servicios programados
    path('schedule/create/', views.schedule_create, name='schedule_create'),
    path('schedule/<uuid:schedule_id>/', views.schedule_detail, name='schedule_detail'),
    path('schedule/<uuid:schedule_id>/edit/', views.schedule_edit, name='schedule_edit'),
    path('schedule/<uuid:schedule_id>/assign/', views.schedule_assign, name='schedule_assign'),
    path('schedule/<uuid:schedule_id>/remove-assignment/<uuid:assignment_id>/', views.schedule_remove_assignment, name='schedule_remove_assignment'),
    path('schedule/<uuid:schedule_id>/delete/', views.schedule_delete, name='schedule_delete'),

    # Generar mes
    path('generate/', views.generate_month, name='generate_month'),

    # Clonar mes
    path('clone/', views.clone_month, name='clone_month'),

    # Reiniciar mes
    path('reset/', views.reset_month, name='reset_month'),

    # Reporte imprimible
    path('report/', views.monthly_report, name='monthly_report'),

    # Colores de mes
    path('month-colors/', views.month_colors, name='month_colors'),
]
