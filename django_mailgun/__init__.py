import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import sanitize_address

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class MailgunAPIError(Exception):
    pass

class MailgunBackend(BaseEmailBackend):
    """A Django Email backend that uses mailgun.
    """

    def __init__(self, fail_silently=False, *args, **kwargs):
        super(MailgunBackend, self).__init__(
                        fail_silently=fail_silently, 
                        *args, **kwargs)

        try:
            self._access_key = getattr(settings, 'MAILGUN_ACCESS_KEY')
            self._server_name = getattr(settings, 'MAILGUN_SERVER_NAME')
        except AttributeError:
            if fail_silently:
                self._access_key, self._server_name = None
            else:
                raise

        self._api_url = "https://api.mailgun.net/v2/%s/" % self._server_name

    def open(self):
        """Stub for open connection, all sends are done over HTTP POSTs
        """
        pass

    def close(self):
        """Close any open HTTP connections to the API server.
        """
        pass

    def _send(self, email_message):
        """A helper method that does the actual sending."""
        if not email_message.recipients():
            return False
        from_email = sanitize_address(email_message.from_email, email_message.encoding)
        to_emails = [sanitize_address(addr, email_message.encoding)
                      for addr in email_message.to]
        bcc_emails = [sanitize_address(addr, email_message.encoding)
                      for addr in email_message.bcc]

        try:
            r = requests.\
                post(self._api_url + "messages.mime",
                     auth=("api", self._access_key),
                     data={
                            "to": ", ".join(to_emails),
                            "bcc": ", ".join(bcc_emails),
                            "from": from_email,
                         },
                     files={
                            "message": StringIO(email_message.message().as_string()),
                         }
                     )
        except:
            if not self.fail_silently:
                raise
            return False

        if r.status_code != 200:
            if not self.fail_silently:
                raise MailgunAPIError(r)
            return False

        return True

    def send_messages(self, email_messages):
        """Sends one or more EmailMessage objects and returns the number of
        email messages sent.
        """
        if not email_messages:
            return

        num_sent = 0
        for message in email_messages:
            if self._send(message):
                num_sent += 1

        return num_sent
