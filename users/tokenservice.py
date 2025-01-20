from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
import uuid

class TokenService:
    """
    Service for generating and revoking JWT tokens for users.
    """

    @staticmethod
    def get_tokens_for_user(user):
        """
        Generate JWT tokens for a user.

        Args:
            user: The user instance to generate tokens for.

        Returns:
            dict: Dictionary containing access and refresh tokens.
        """
        refresh = RefreshToken.for_user(user)
        token_id = str(uuid.uuid4())
        issued_at = timezone.now().timestamp()

        refresh.payload.update({
            'token_type': 'refresh',
            'jti': token_id,
            'iat': issued_at,
            'user_id': str(user.id),
            'email': user.email,
            'is_verified': user.is_verified,
        })

        access = refresh.access_token
        access.payload.update({
            'token_type': 'access',
            'jti': str(uuid.uuid4()),
            'iat': issued_at,
            'user_id': str(user.id),
            'email': user.email,
            'is_verified': user.is_verified,
        })

        return {
            'refresh': str(refresh),
            'access': str(access),
        }

    @staticmethod
    def revoke_user_tokens(user):
        """
        Revoke all refresh tokens for a user.

        Args:
            user: The user instance whose tokens should be revoked.
        """
        RefreshToken.objects.filter(user=user).delete()