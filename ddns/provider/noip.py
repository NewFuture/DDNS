# coding=utf-8
"""
No-IP (noip.com) Dynamic DNS API
@author: GitHub Copilot
"""

import base64
from ._base import SimpleProvider, TYPE_FORM


class NoipProvider(SimpleProvider):
    """
    No-IP (www.noip.com) Dynamic DNS Provider

    No-IP is a popular dynamic DNS service that provides simple HTTP-based
    API for updating DNS records. This provider supports the standard
    No-IP update protocol.
    """

    endpoint = "https://dynupdate.no-ip.com"
    content_type = TYPE_FORM
    accept = None  # No-IP returns plain text response
    decode_response = False  # Response is plain text, not JSON

    def _validate(self):
        """
        Validate authentication credentials for No-IP
        """
        if not self.auth_id:
            raise ValueError("No-IP requires username as 'id'")
        if not self.auth_token:
            raise ValueError("No-IP requires password as 'token'")

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        """
        Update DNS record using No-IP Dynamic Update API

        No-IP API Reference:
        - URL: https://dynupdate.no-ip.com/nic/update
        - Method: GET or POST
        - Authentication: HTTP Basic Auth (username:password)
        - Parameters:
          - hostname: The hostname to update
          - myip: The IP address to set (optional, uses client IP
                  if not provided)

        Response codes:
        - good: Update successful
        - nochg: IP address is current, no update performed
        - nohost: Hostname supplied does not exist
        - badauth: Invalid username/password combination
        - badagent: Client disabled
        - !donator: An update request was sent including a feature that
                    is not available
        - abuse: Username is blocked due to abuse
        """
        self.logger.info("%s => %s(%s)", domain, value, record_type)

        # Prepare request parameters
        params = {"hostname": domain, "myip": value}

        # Prepare HTTP Basic Authentication headers
        auth_string = "{0}:{1}".format(self.auth_id, self.auth_token)
        if not isinstance(auth_string, bytes):  # Python 3
            auth_bytes = auth_string.encode("utf-8")
        else:  # Python 2
            auth_bytes = auth_string

        auth_b64 = base64.b64encode(auth_bytes).decode("ascii")
        headers = {
            "Authorization": "Basic {0}".format(auth_b64),
            "User-Agent": "DDNS/{0} (ddns@newfuture.cc)".format(self.version),
        }

        try:
            # Use GET request as it's the most common method for DDNS
            response = self._http("GET", "/nic/update", queries=params, headers=headers)

            if response is not None:
                response_str = str(response).strip()
                self.logger.info("No-IP API response: %s", response_str)

                # Check for successful responses
                if response_str.startswith("good") or response_str.startswith("nochg"):
                    return True
                elif response_str.startswith("nohost"):
                    self.logger.error("Hostname %s does not exist under No-IP account", domain)
                elif response_str.startswith("badauth"):
                    self.logger.error("Invalid No-IP username/password combination")
                elif response_str.startswith("badagent"):
                    self.logger.error("No-IP client disabled")
                elif response_str.startswith("!donator"):
                    self.logger.error("Feature not available for No-IP free account")
                elif response_str.startswith("abuse"):
                    self.logger.error("No-IP account blocked due to abuse")
                else:
                    self.logger.error("Unexpected No-IP API response: %s", response_str)
            else:
                self.logger.error("Empty response from No-IP API")

        except Exception as e:
            self.logger.error("Error updating No-IP record for %s: %s", domain, e)

        return False
