from django.conf import settings
from rest_framework.settings import (
    APISettings,
    perform_import,
)
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _


class TrenchAPISettings(APISettings):

    @property
    def user_settings(self):
        if not hasattr(self, '_user_settings'):
            self._user_settings = getattr(settings, 'TRENCH_AUTH', {})
        return self._user_settings

    def __getattr__(self, attr):

        if attr not in self.defaults:
            raise AttributeError("Invalid API setting: '%s'" % attr)
        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Coerce import strings into classes
        if attr in self.import_strings:
            val = perform_import(val, attr)

        # Validations for attrs
        if attr == 'BACKUP_CODES_CHARACTERS' and ',' in val:
            raise ImproperlyConfigured(
                'Cannot use , as a character for {}.'.format(attr),
            )
        if attr == 'MFA_METHODS':
            for method_name, method_config in val.items():
                if 'HANDLER' not in method_config:
                    raise ImproperlyConfigured(
                        'Missing handler in {} configuration.'.format(
                            method_name
                        ),
                    )
                method_config['HANDLER'] = perform_import(
                    method_config.get('HANDLER'),
                    'HANDLER',
                )
        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def __getitem__(self, attr):
        return self.__getattr__(attr)


DEFAULTS = {
    'FROM_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL'),
    'USER_MFA_MODEL': 'trench.MFAMethod',
    'USER_ACTIVE_FIELD': 'is_active',
    'BACKUP_CODES_QUANTITY': 5,
    'BACKUP_CODES_LENGTH': 6,  # keep (quantity * length) under 200
    'BACKUP_CODES_CHARACTERS': (
        '0123456789'
    ),
    'DEFAULT_VALIDITY_PERIOD': 30,
    'CONFIRM_DISABLE_WITH_CODE': False,
    'CONFIRM_BACKUP_CODES_REGENERATION_WITH_CODE': True,
    'ALLOW_BACKUP_CODES_REGENERATION': True,
    'APPLICATION_ISSUER_NAME': 'MyApplication',
    'CACHE_PREFIX': 'trench',
    'MAX_METHODS_PER_USER': 3,
    'MFA_METHODS': {
        'sms': {
            'VERBOSE_NAME': _('sms'),
            'VALIDITY_PERIOD': 60 * 10,
            'HANDLER': 'trench.backends.twilio.TwilioBackend',
            'SOURCE_FIELD': 'phone_number',
            'TWILIO_ACCOUNT_SID': 'YOUR KEY',
            'TWILIO_AUTH_TOKEN': 'YOUR KEY',
            'TWILIO_VERIFIED_FROM_NUMBER': 'YOUR TWILIO REGISTERED NUMBER',
        },
        'email': {
            'VERBOSE_NAME': _('email'),
            'VALIDITY_PERIOD': 60 * 10,
            'HANDLER': 'trench.backends.templated_mail.TemplatedMailBackend',
            'SOURCE_FIELD': 'email',
        },
        'app': {
            'VERBOSE_NAME': _('app'),
            'VALIDITY_PERIOD': 60 * 10,
            'USES_THIRD_PARTY_CLIENT': True,
            'HANDLER': 'trench.backends.application.ApplicationBackend',
        },
    },
}

api_settings = TrenchAPISettings(None, DEFAULTS, None)
