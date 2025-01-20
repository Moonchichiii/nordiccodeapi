from django.core.mail.backends.smtp import EmailBackend
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from django.conf import settings
import smtplib

class GmailOAuth2Backend(EmailBackend):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.credentials = None

    def _refresh_credentials(self):
        """Refresh OAuth2 credentials."""
        self.credentials = Credentials(
            None,  # No access token needed initially
            refresh_token=settings.GOOGLE_OAUTH2_REFRESH_TOKEN,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
            client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
            scopes=['https://www.googleapis.com/auth/gmail.send']
        )
        
        # Refresh the credentials
        self.credentials.refresh(Request())
        return self.credentials.token

    def open(self):
        """Initialize connection with OAuth2."""
        if self.connection:
            return False

        try:
            self.connection = smtplib.SMTP(self.host, self.port)
            if self.use_tls:
                self.connection.starttls()
            
            # Get fresh access token and authenticate
            access_token = self._refresh_credentials()
            auth_string = f"user={self.username}\1auth=Bearer {access_token}\1\1"
            self.connection.docmd('AUTH', 'XOAUTH2 ' + auth_string.encode('base64').decode('ascii'))
            
            return True
        except Exception as e:
            print(f"Failed to establish SMTP connection: {str(e)}")
            return False