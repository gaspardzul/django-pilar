from .models import OrganizationMembership


def get_user_primary_organization(user):
    """
    Get the primary organization for a user.
    Returns the organization where they are owner, or the first active membership.
    """
    if not user.is_authenticated:
        return None
    
    # Try to get organization where user is owner
    membership = OrganizationMembership.objects.filter(
        user=user,
        role='owner',
        is_active=True
    ).first()
    
    # If not owner, get any active membership
    if not membership:
        membership = OrganizationMembership.objects.filter(
            user=user,
            is_active=True
        ).order_by('-joined_at').first()
    
    return membership.organization_schema if membership else None


def get_user_organization_url(user, request):
    """
    Get the URL for the user's primary organization.
    """
    schema_name = get_user_primary_organization(user)
    
    if not schema_name:
        return None
    
    # Get the protocol and port
    protocol = 'https' if request.is_secure() else 'http'
    port = request.get_port()
    port_str = f':{port}' if port and port not in ['80', '443'] else ''
    
    # Build the URL
    # In production, you'd use the actual domain
    # For development, we use .localhost
    domain = f"{schema_name}.localhost{port_str}"
    
    return f"{protocol}://{domain}/dashboard/"
