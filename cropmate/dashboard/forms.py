from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class LoginForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-input w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-300 bg-white',
            'id': 'email',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-300 bg-white',
            'id': 'password',
        })
    )


class SignupForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-300 bg-white',
            'id': 'username',
        })
    )
    email = forms.CharField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-input w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-300 bg-white',
            'id': 'email',
        })
    )
    password1 = forms.CharField(
        label='Password',
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-300 bg-white',
            'id': 'password1',
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-300 bg-white',
            'id': 'password2',
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # Simple check for @ symbol
        if '@' not in email:
            raise ValidationError("Email must contain '@' symbol.")
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        
        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        
        # Check minimum 8 characters
        if len(password1) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        # Check if passwords match
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match.")
        
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        # Set password using set_password to properly hash it
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user