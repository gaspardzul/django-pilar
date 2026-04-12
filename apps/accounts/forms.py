from allauth.account.forms import SignupForm
from django import forms


class CustomSignupForm(SignupForm):
    organization_name = forms.CharField(
        max_length=100,
        label='Organization Name',
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., First Baptist Church',
            'class': 'border-b-2 border-t-0 border-x-0 border-black p-3 w-full focus:border-dark-gray focus:outline-none'
        }),
        help_text='This will be the name of your organization/church'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update existing field classes to match design
        self.fields['email'].widget.attrs.update({
            'class': 'border-b-2 border-t-0 border-x-0 border-black p-3 w-full focus:border-dark-gray focus:outline-none',
            'placeholder': 'Email address'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'border-b-2 border-t-0 border-x-0 border-black p-3 w-full focus:border-dark-gray focus:outline-none',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'border-b-2 border-t-0 border-x-0 border-black p-3 w-full focus:border-dark-gray focus:outline-none',
            'placeholder': 'Confirm password'
        })
    
    def save(self, request):
        user = super().save(request)
        # Store organization name in session for the signal to use
        request.session['organization_name'] = self.cleaned_data.get('organization_name')
        return user
