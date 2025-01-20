from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone


class AccountLockoutService:
    """
    Service to handle account lockout after a number of failed login attempts.
    """
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 15 * 60

    @classmethod
    def check_and_update_login_attempts(cls, email):
        """
        Check and update the number of login attempts for the given email.
        Lock the account if the maximum number of attempts is exceeded.
        """
        UserModel = get_user_model()
        cache_key = f"login_attempts_{email}"
        login_attempts = cache.get(cache_key, {"count": 0, "first_attempt_time": None})
        current_time = timezone.now().timestamp()

        if login_attempts["first_attempt_time"] and current_time - login_attempts["first_attempt_time"] > cls.LOCKOUT_DURATION:
            login_attempts = {"count": 1, "first_attempt_time": current_time}
        else:
            login_attempts["count"] += 1

        if not login_attempts["first_attempt_time"]:
            login_attempts["first_attempt_time"] = current_time

        cache.set(cache_key, login_attempts, cls.LOCKOUT_DURATION)

        if login_attempts["count"] > cls.MAX_LOGIN_ATTEMPTS:
            try:
                user = UserModel.objects.get(email=email)
                user.is_active = False
                user.save()
                return False
            except UserModel.DoesNotExist:
                return False

        return True

    @classmethod
    def reset_login_attempts(cls, email):
        """
        Reset the login attempts for the given email.
        """
        cache.delete(f"login_attempts_{email}")

    @classmethod
    def unlock_account(cls, email):
        """
        Unlock the account for the given email.
        """
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=email)
            user.is_active = True
            user.save()
            cache.delete(f"login_attempts_{email}")
            return True
        except UserModel.DoesNotExist:
            return False
