from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers

class CustomRegisterSerializer(RegisterSerializer):
    # Basic personal fields
    full_name = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)

    # Address / billing info
    street_address = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    state_or_region = serializers.CharField(required=False, allow_blank=True)
    postal_code = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    vat_number = serializers.CharField(required=False, allow_blank=True)

    # Legal compliance fields
    accepted_terms = serializers.BooleanField(required=True)
    marketing_consent = serializers.BooleanField(required=False, default=False)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data.update({
            "full_name": self.validated_data.get("full_name", ""),
            "phone_number": self.validated_data.get("phone_number", ""),
            "street_address": self.validated_data.get("street_address", ""),
            "city": self.validated_data.get("city", ""),
            "state_or_region": self.validated_data.get("state_or_region", ""),
            "postal_code": self.validated_data.get("postal_code", ""),
            "country": self.validated_data.get("country", ""),
            "vat_number": self.validated_data.get("vat_number", ""),
            "accepted_terms": self.validated_data.get("accepted_terms", False),
            "marketing_consent": self.validated_data.get("marketing_consent", False),
        })
        return data
