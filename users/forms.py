from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.validators import RegexValidator

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """
    Form for creating a new CustomUser in the admin interface.
    Follows Django's best practices for user creation forms.
    """

    email = forms.EmailField(
        required=True,
        help_text="Enter a valid email address",
        validators=[],
    )
    full_name = forms.CharField(
        max_length=150, required=False, help_text="Optional: Enter your full name"
    )
    phone_number = forms.CharField(
        max_length=30,
        required=False,
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,15}$",
                message="Phone number must be in format: '+999999999'. Up to 15 digits.",
            )
        ],
    )
    accepted_terms = forms.BooleanField(
        required=True, help_text="You must accept the Terms of Service"
    )
    marketing_consent = forms.BooleanField(
        required=False, help_text="Optional: Receive marketing communications"
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = (
            "email",
            "password1",
            "password2",
            "full_name",
            "phone_number",
            "accepted_terms",
            "marketing_consent",
        )

    def save(self, commit=True):
        """
        Override save method to ensure proper user creation
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        user.full_name = self.cleaned_data.get("full_name", "")
        user.accepted_terms = self.cleaned_data["accepted_terms"]
        user.marketing_consent = self.cleaned_data.get("marketing_consent", False)

        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    """
    Form for updating a CustomUser in the admin interface.
    Provides controlled update capabilities.
    """

    class Meta:
        model = CustomUser
        fields = (
            "email",
            "full_name",
            "phone_number",
            "is_active",
            "is_verified",
            "marketing_consent",
        )

    def clean_email(self):
        """
        Ensure email is lowercase and unique
        """
        email = self.cleaned_data.get("email")
        if email:
            email = email.lower()
            qs = CustomUser.objects.exclude(pk=self.instance.pk)
            if qs.filter(email=email).exists():
                raise forms.ValidationError("This email is already in use.")
        return email
