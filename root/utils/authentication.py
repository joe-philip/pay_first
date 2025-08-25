from django.utils.translation import gettext_lazy
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

from main.utils import is_auth_token_expired


class ExpiringTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise AuthenticationFailed(gettext_lazy('Invalid token.'))

        if not token.user.is_active:
            raise AuthenticationFailed(
                gettext_lazy('User inactive or deleted.'))
        if is_auth_token_expired(token):
            raise AuthenticationFailed(
                gettext_lazy("Session Expired, please login again")
            )
        return (token.user, token)
