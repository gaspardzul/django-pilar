from allauth.account.adapter import DefaultAccountAdapter
from django.shortcuts import resolve_url
from .utils import get_user_organization_url


class CustomAccountAdapter(DefaultAccountAdapter):
    
    def get_login_redirect_url(self, request):
        """
        Redirect user to their organization's dashboard after login.
        """
        # Get the user's primary organization URL
        org_url = get_user_organization_url(request.user, request)
        
        if org_url:
            return org_url
        
        # Fallback to default behavior
        return resolve_url(self.get_setting('LOGIN_REDIRECT_URL'))
