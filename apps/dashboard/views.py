import secrets

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import (
    SubscriptionPlan, UserSettings,
    Member, Ministry, Family, MemberMinistry, FamilyMember
)
from .tasks import (
    send_subscription_cancellation_email,
    send_subscription_confirmation_email,
    send_trial_started_email,
)


@login_required
@require_http_methods(['GET'])
def dashboard_home(request):
    # Get statistics
    total_members = Member.objects.filter(status='active').count()
    total_ministries = Ministry.objects.filter(active=True).count()
    total_families = Family.objects.count()
    
    # Recent members (last 5)
    recent_members = Member.objects.all().order_by('-created_at')[:5]
    
    context = {
        'total_members': total_members,
        'total_ministries': total_ministries,
        'total_families': total_families,
        'recent_members': recent_members,
    }
    return render(request, 'dashboard/home.html', context)

@login_required
@require_http_methods(['GET', 'POST'])
def profile(request):
    if request.method == 'POST':
        # Handle profile update
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('dashboard:profile')
    return render(request, 'dashboard/profile.html')

@login_required
@require_http_methods(['GET', 'POST'])
def settings(request):
    user_settings, created = UserSettings.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_settings.notify_comments = request.POST.get('comments') == 'on'
        user_settings.notify_updates = request.POST.get('updates') == 'on'
        user_settings.notify_marketing = request.POST.get('marketing') == 'on'
        user_settings.save()

        messages.success(request, 'Settings updated successfully.')
        return redirect('dashboard:settings')

    # Check if a new API key was just generated (stored in session)
    new_api_key = request.session.pop('new_api_key', None)

    context = {
        'notification_settings': {
            'comments': user_settings.notify_comments,
            'updates': user_settings.notify_updates,
            'marketing': user_settings.notify_marketing,
        },
        'subscription': {
            'plan': user_settings.subscription_plan,
            'plan_name': user_settings.subscription_plan.name if user_settings.subscription_plan else None,
            'status': user_settings.subscription_status,
            'is_active': user_settings.is_subscription_active,
            'is_trial': user_settings.is_trial_active,
            'start_date': user_settings.subscription_start_date,
            'end_date': user_settings.subscription_end_date,
            'trial_end_date': user_settings.trial_end_date,
        },
        'api': {
            'has_key': bool(user_settings.api_key),
            'key_created_at': user_settings.api_key_created_at,
            'new_key': new_api_key,
        },
    }
    return render(request, 'dashboard/settings.html', context)

@login_required
@require_http_methods(['POST'])
def generate_api_key(request):
    user_settings, created = UserSettings.objects.get_or_create(user=request.user)

    api_key = secrets.token_urlsafe(32)
    user_settings.api_key = api_key
    user_settings.api_key_created_at = timezone.now()
    user_settings.save()

    # Store the key in session so it can be shown once on the settings page
    request.session['new_api_key'] = api_key

    messages.success(request, 'API key generated. Copy it now — it won\'t be shown again.')
    return redirect('dashboard:settings')

@login_required
@require_http_methods(['GET'])
def subscription_plans(request):
    plans = SubscriptionPlan.objects.filter(is_active=True)
    user_settings, created = UserSettings.objects.get_or_create(user=request.user)

    context = {
        'plans': plans,
        'current_plan': user_settings.subscription_plan,
        'subscription_status': user_settings.subscription_status,
        'is_subscription_active': user_settings.is_subscription_active,
        'is_trial_active': user_settings.is_trial_active,
    }
    return render(request, 'dashboard/subscription_plans.html', context)

@login_required
@require_http_methods(['POST'])
def subscribe_to_plan(request, plan_slug):
    plan = get_object_or_404(SubscriptionPlan, slug=plan_slug, is_active=True)
    user_settings = UserSettings.objects.get(user=request.user)

    # Check if user already has an active subscription
    if user_settings.is_subscription_active:
        messages.warning(request, 'You already have an active subscription.')
        return redirect('dashboard:subscription_plans')

    # Update user settings with new subscription
    user_settings.subscription_plan = plan
    user_settings.subscription_status = 'active'
    user_settings.subscription_start_date = timezone.now()

    # Set subscription end date based on interval
    if plan.interval == 'monthly':
        user_settings.subscription_end_date = timezone.now() + timezone.timedelta(days=30)
    else:  # yearly
        user_settings.subscription_end_date = timezone.now() + timezone.timedelta(days=365)

    user_settings.save()

    send_subscription_confirmation_email.enqueue(
        user_email=request.user.email,
        plan_name=plan.name,
    )

    messages.success(request, f'Successfully subscribed to {plan.name} plan.')
    return redirect('dashboard:settings')

@login_required
@require_http_methods(['POST'])
def cancel_subscription(request):
    user_settings = UserSettings.objects.get(user=request.user)

    if not user_settings.is_subscription_active:
        messages.warning(request, 'You do not have an active subscription to cancel.')
        return redirect('dashboard:settings')

    user_settings.subscription_status = 'cancelled'
    user_settings.save()

    send_subscription_cancellation_email.enqueue(user_email=request.user.email)

    messages.success(request, 'Your subscription has been cancelled.')
    return redirect('dashboard:settings')

@login_required
@require_http_methods(['POST'])
def start_trial(request):
    user_settings = UserSettings.objects.get(user=request.user)

    if user_settings.is_subscription_active or user_settings.is_trial_active:
        messages.warning(request, 'You already have an active subscription or trial.')
        return redirect('dashboard:subscription_plans')

    # Start trial period (14 days)
    user_settings.subscription_status = 'trial'
    user_settings.trial_end_date = timezone.now() + timezone.timedelta(days=14)
    user_settings.save()

    send_trial_started_email.enqueue(user_email=request.user.email)

    messages.success(request, 'Trial period started successfully.')
    return redirect('dashboard:settings')


# ============================================
# CHURCH MANAGEMENT VIEWS
# ============================================

# Members Views
@login_required
@require_http_methods(['GET'])
def members_list(request):
    members = Member.objects.all().order_by('last_name', 'first_name')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        members = members.filter(status=status_filter)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        members = members.filter(
            models.Q(first_name__icontains=search_query) |
            models.Q(last_name__icontains=search_query) |
            models.Q(email__icontains=search_query)
        )
    
    context = {
        'members': members,
        'total_members': Member.objects.filter(status='active').count(),
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'dashboard/members/list.html', context)


@login_required
@require_http_methods(['GET'])
def member_detail(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    
    # Get ministries
    ministries = member.ministry_memberships.filter(end_date__isnull=True)
    
    # Get family relationships
    families = member.family_relationships.filter(end_date__isnull=True)
    
    # Get available ministries (not already in)
    current_ministry_ids = ministries.values_list('ministry_id', flat=True)
    available_ministries = Ministry.objects.filter(active=True).exclude(id__in=current_ministry_ids).order_by('name')
    
    # Get available families (not already in)
    current_family_ids = families.values_list('family_id', flat=True)
    available_families = Family.objects.exclude(id__in=current_family_ids).order_by('family_name')
    
    context = {
        'member': member,
        'ministries': ministries,
        'families': families,
        'available_ministries': available_ministries,
        'available_families': available_families,
    }
    return render(request, 'dashboard/members/detail.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def member_create(request):
    if request.method == 'POST':
        member = Member.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            date_of_birth=request.POST.get('date_of_birth') or None,
            gender=request.POST.get('gender', ''),
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            address=request.POST.get('address', ''),
            join_date=request.POST.get('join_date') or None,
            status=request.POST.get('status', 'active'),
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, f'Member {member.get_full_name()} created successfully.')
        return redirect('dashboard:member_detail', member_id=member.id)
    
    return render(request, 'dashboard/members/form.html', {'action': 'Create'})


@login_required
@require_http_methods(['GET', 'POST'])
def member_edit(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    
    if request.method == 'POST':
        member.first_name = request.POST.get('first_name')
        member.last_name = request.POST.get('last_name')
        member.date_of_birth = request.POST.get('date_of_birth') or None
        member.gender = request.POST.get('gender', '')
        member.email = request.POST.get('email', '')
        member.phone = request.POST.get('phone', '')
        member.address = request.POST.get('address', '')
        member.join_date = request.POST.get('join_date') or None
        member.status = request.POST.get('status', 'active')
        member.notes = request.POST.get('notes', '')
        member.save()
        
        messages.success(request, f'Member {member.get_full_name()} updated successfully.')
        return redirect('dashboard:member_detail', member_id=member.id)
    
    context = {'member': member, 'action': 'Edit'}
    return render(request, 'dashboard/members/form.html', context)


@login_required
@require_http_methods(['POST'])
def member_add_to_ministry(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    ministry_id = request.POST.get('ministry_id')
    
    if ministry_id:
        ministry = get_object_or_404(Ministry, id=ministry_id)
        
        # Check if member is already in this ministry
        existing = MemberMinistry.objects.filter(
            ministry=ministry,
            member=member,
            end_date__isnull=True
        ).exists()
        
        if existing:
            messages.warning(request, f'Ya estás en el ministerio {ministry.name}.')
        else:
            MemberMinistry.objects.create(
                ministry=ministry,
                member=member,
                role=request.POST.get('role', 'member'),
                start_date=request.POST.get('start_date') or None,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, f'Agregado al ministerio {ministry.name} exitosamente.')
    
    return redirect('dashboard:member_detail', member_id=member_id)


@login_required
@require_http_methods(['POST'])
def member_add_to_family(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    family_id = request.POST.get('family_id')
    
    if family_id:
        family = get_object_or_404(Family, id=family_id)
        
        # Check if member is already in this family
        existing = FamilyMember.objects.filter(
            family=family,
            member=member,
            end_date__isnull=True
        ).exists()
        
        if existing:
            messages.warning(request, f'Ya estás en la familia {family.family_name}.')
        else:
            family_member = FamilyMember.objects.create(
                family=family,
                member=member,
                relationship_type=request.POST.get('relationship_type'),
                is_primary_contact=request.POST.get('is_primary_contact') == 'on',
                notes=request.POST.get('notes', ''),
            )
            
            # Update family primary contact if requested
            if family_member.is_primary_contact:
                family.primary_contact = member
                family.save()
            
            messages.success(request, f'Agregado a la familia {family.family_name} exitosamente.')
    
    return redirect('dashboard:member_detail', member_id=member_id)


# Ministries Views
@login_required
@require_http_methods(['GET'])
def ministries_list(request):
    ministries = Ministry.objects.all().order_by('name')
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        ministries = ministries.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by active status
    active_filter = request.GET.get('active')
    if active_filter == 'true':
        ministries = ministries.filter(active=True)
    elif active_filter == 'false':
        ministries = ministries.filter(active=False)
    
    context = {
        'ministries': ministries,
        'total_ministries': Ministry.objects.filter(active=True).count(),
        'active_filter': active_filter,
        'search_query': search_query,
    }
    return render(request, 'dashboard/ministries/list.html', context)


@login_required
@require_http_methods(['GET'])
def ministry_detail(request, ministry_id):
    ministry = get_object_or_404(Ministry, id=ministry_id)
    
    # Get active members
    active_members = ministry.get_active_members()
    
    # Get leaders count
    leaders_count = active_members.filter(role__in=['leader', 'co_leader']).count()
    
    # Get available members (not already in this ministry)
    current_member_ids = active_members.values_list('member_id', flat=True)
    available_members = Member.objects.filter(status='active').exclude(id__in=current_member_ids).order_by('last_name', 'first_name')
    
    context = {
        'ministry': ministry,
        'active_members': active_members,
        'leaders_count': leaders_count,
        'available_members': available_members,
    }
    return render(request, 'dashboard/ministries/detail.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def ministry_create(request):
    if request.method == 'POST':
        ministry = Ministry.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description', ''),
            active=request.POST.get('active') == 'on',
        )
        
        # Set leader if provided
        leader_id = request.POST.get('leader')
        if leader_id:
            ministry.leader = Member.objects.get(id=leader_id)
            ministry.save()
        
        messages.success(request, f'Ministry {ministry.name} created successfully.')
        return redirect('dashboard:ministry_detail', ministry_id=ministry.id)
    
    members = Member.objects.filter(status='active').order_by('last_name', 'first_name')
    return render(request, 'dashboard/ministries/form.html', {'action': 'Create', 'members': members})


@login_required
@require_http_methods(['GET', 'POST'])
def ministry_edit(request, ministry_id):
    ministry = get_object_or_404(Ministry, id=ministry_id)
    
    if request.method == 'POST':
        ministry.name = request.POST.get('name')
        ministry.description = request.POST.get('description', '')
        ministry.active = request.POST.get('active') == 'on'
        
        # Update leader if provided
        leader_id = request.POST.get('leader')
        if leader_id:
            ministry.leader = Member.objects.get(id=leader_id)
        else:
            ministry.leader = None
        
        ministry.save()
        
        messages.success(request, f'Ministry {ministry.name} updated successfully.')
        return redirect('dashboard:ministry_detail', ministry_id=ministry.id)
    
    members = Member.objects.filter(status='active').order_by('last_name', 'first_name')
    context = {'ministry': ministry, 'action': 'Edit', 'members': members}
    return render(request, 'dashboard/ministries/form.html', context)


@login_required
@require_http_methods(['POST'])
def ministry_add_member(request, ministry_id):
    ministry = get_object_or_404(Ministry, id=ministry_id)
    member_id = request.POST.get('member_id')
    
    if member_id:
        member = get_object_or_404(Member, id=member_id)
        
        # Check if member is already in this ministry
        existing = MemberMinistry.objects.filter(
            ministry=ministry,
            member=member,
            end_date__isnull=True
        ).exists()
        
        if existing:
            messages.warning(request, f'{member.get_full_name()} ya está en este ministerio.')
        else:
            MemberMinistry.objects.create(
                ministry=ministry,
                member=member,
                role=request.POST.get('role', 'member'),
                start_date=request.POST.get('start_date') or None,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, f'{member.get_full_name()} agregado al ministerio exitosamente.')
    
    return redirect('dashboard:ministry_detail', ministry_id=ministry_id)


@login_required
@require_http_methods(['POST'])
def ministry_remove_member(request, ministry_id, member_ministry_id):
    ministry = get_object_or_404(Ministry, id=ministry_id)
    member_ministry = get_object_or_404(MemberMinistry, id=member_ministry_id, ministry=ministry)
    
    member_name = member_ministry.member.get_full_name()
    member_ministry.delete()
    
    messages.success(request, f'{member_name} removido del ministerio.')
    return redirect('dashboard:ministry_detail', ministry_id=ministry_id)


# Families Views
@login_required
@require_http_methods(['GET'])
def families_list(request):
    families = Family.objects.all().order_by('family_name')
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        families = families.filter(family_name__icontains=search_query)
    
    context = {
        'families': families,
        'total_families': Family.objects.count(),
        'search_query': search_query,
    }
    return render(request, 'dashboard/families/list.html', context)


@login_required
@require_http_methods(['GET'])
def family_detail(request, family_id):
    family = get_object_or_404(Family, id=family_id)
    
    # Get family structure
    structure = family.get_family_structure()
    all_members = family.get_family_members()
    
    # Get available members (not already in this family)
    current_member_ids = all_members.values_list('member_id', flat=True)
    available_members = Member.objects.filter(status='active').exclude(id__in=current_member_ids).order_by('last_name', 'first_name')
    
    context = {
        'family': family,
        'structure': structure,
        'all_members': all_members,
        'available_members': available_members,
    }
    return render(request, 'dashboard/families/detail.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def family_create(request):
    if request.method == 'POST':
        family = Family.objects.create(
            family_name=request.POST.get('family_name'),
            address=request.POST.get('address', ''),
            notes=request.POST.get('notes', ''),
        )
        
        # Set primary contact if provided
        primary_contact_id = request.POST.get('primary_contact')
        if primary_contact_id:
            family.primary_contact = Member.objects.get(id=primary_contact_id)
            family.save()
        
        messages.success(request, f'Family {family.family_name} created successfully.')
        return redirect('dashboard:family_detail', family_id=family.id)
    
    members = Member.objects.filter(status='active').order_by('last_name', 'first_name')
    return render(request, 'dashboard/families/form.html', {'action': 'Create', 'members': members})


@login_required
@require_http_methods(['GET', 'POST'])
def family_edit(request, family_id):
    family = get_object_or_404(Family, id=family_id)
    
    if request.method == 'POST':
        family.family_name = request.POST.get('family_name')
        family.address = request.POST.get('address', '')
        family.notes = request.POST.get('notes', '')
        
        # Update primary contact if provided
        primary_contact_id = request.POST.get('primary_contact')
        if primary_contact_id:
            family.primary_contact = Member.objects.get(id=primary_contact_id)
        else:
            family.primary_contact = None
        
        family.save()
        
        messages.success(request, f'Family {family.family_name} updated successfully.')
        return redirect('dashboard:family_detail', family_id=family.id)
    
    members = Member.objects.filter(status='active').order_by('last_name', 'first_name')
    context = {'family': family, 'action': 'Edit', 'members': members}
    return render(request, 'dashboard/families/form.html', context)


@login_required
@require_http_methods(['POST'])
def family_add_member(request, family_id):
    family = get_object_or_404(Family, id=family_id)
    member_id = request.POST.get('member_id')
    
    if member_id:
        member = get_object_or_404(Member, id=member_id)
        
        # Check if member is already in this family
        existing = FamilyMember.objects.filter(
            family=family,
            member=member,
            end_date__isnull=True
        ).exists()
        
        if existing:
            messages.warning(request, f'{member.get_full_name()} ya está en esta familia.')
        else:
            family_member = FamilyMember.objects.create(
                family=family,
                member=member,
                relationship_type=request.POST.get('relationship_type'),
                is_primary_contact=request.POST.get('is_primary_contact') == 'on',
                notes=request.POST.get('notes', ''),
            )
            
            # Update family primary contact if requested
            if family_member.is_primary_contact:
                family.primary_contact = member
                family.save()
            
            messages.success(request, f'{member.get_full_name()} agregado a la familia exitosamente.')
    
    return redirect('dashboard:family_detail', family_id=family_id)


@login_required
@require_http_methods(['POST'])
def family_remove_member(request, family_id, family_member_id):
    family = get_object_or_404(Family, id=family_id)
    family_member = get_object_or_404(FamilyMember, id=family_member_id, family=family)
    
    member_name = family_member.member.get_full_name()
    family_member.delete()
    
    messages.success(request, f'{member_name} removido de la familia.')
    return redirect('dashboard:family_detail', family_id=family_id)
