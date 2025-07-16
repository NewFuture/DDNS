# coding=utf-8
"""
No-IP (noip.com) Dynamic DNS API
@author: GitHub Copilot
"""

from ._base import SimpleProvider, TYPE_FORM, quote


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
        Validate authentication credentials for No-IP and update endpoint with auth
        """
        # Check endpoint first
        if not self.endpoint or "://" not in self.endpoint:
            raise ValueError("API endpoint must be defined and contain protocol")

        if not self.id:
            raise ValueError("No-IP requires username as 'id'")
        if not self.token:
            raise ValueError("No-IP requires password as 'token'")

        # Update endpoint with URL-encoded auth credentials
        protocol, domain = self.endpoint.split("://", 1)
        self.endpoint = "{0}://{1}:{2}@{3}".format(
            protocol, quote(self.id, safe=""), quote(self.token, safe=""), domain
        )

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

        try:
            # Use GET request as it's the most common method for DDNS
            # Endpoint already includes auth credentials from _validate()
            response = self._http("GET", "/nic/update", queries=params)

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
