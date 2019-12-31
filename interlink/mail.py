import poplib
import email
import logging


logger = logging.getLogger(__name__)


class PopMailChecker(object):

    """A class for fetching mail"""

    def __init__(self, mailing_list, _logger=None):
        self.mailing_list = mailing_list
        self.logger = _logger or logger

    def fetch_mail(self):
        """Pops mail from the pop server and writes them as IncomingMail"""
        self.logger.debug("Checking mail for: %s" % self.mailing_list.name)
        pop_client = poplib.POP3_SSL(self.mailing_list.pop_host, self.mailing_list.pop_port)
        try:
            # Start with the username
            response = pop_client.user(self.mailing_list.username).decode("utf-8")
            if not response.startswith('+OK'):
                raise Exception('Username not accepted: %s' % response)

            # Password is a bit trickier as this is when the connection magic happens
            try:
                response = pop_client.pass_(self.mailing_list.password).decode("utf-8")
                if not response.startswith('+OK'):
                    raise Exception('Password not accepted: %s' % response)
            except poplib.error_proto as e:
                self.logger.error("Error Connecing: %s" % str(e))
                # We get this back a lot, and we don't want it to flood our logs:
                # error_proto('-ERR [IN-USE] Unable to lock maildrop: Mailbox is locked by POP server',)
                if 'IN-USE' not in str(e):
                    raise e
                self.logger.debug("Ignoring locked mailbox")
                return

            self.logger.debug("Auth Response: '%s'" % response)
            stats = pop_client.stat()
            if stats[0] == 0:
                self.logger.debug("No mail")
                return []

            results = []
            self.logger.info("Processing %d %s 'messages'" % (stats[0], self.mailing_list.name))
            for i in range(stats[0]):
                try:
                    response, mail, _size = pop_client.retr(i + 1)
                    parser = email.parser.BytesFeedParser()
                    parser.feed(b'\n'.join(mail))
                    message = parser.close()

                    # Delete and ignore auto responses
                    if message['Auto-Submitted'] and message['Auto-Submitted'] != 'no':
                        pop_client.dele(i + 1)
                        continue

                    # Delete and ignore messages sent from any list to avoid loops
                    if message['List-ID']:
                        pop_client.dele(i + 1)
                        continue

                    # TODO Delete and ignore soft bounces
                    results.append(self.mailing_list.create_incoming(message))
                    pop_client.dele(i + 1)
                except Exception as e:
                    self.logger.error("Exception while processing email")
                    # self.logger.error("Message: " + str(message))
                    self.logger.error("Exception: " + str(e))

        finally:
            pop_client.quit()

        return results


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
