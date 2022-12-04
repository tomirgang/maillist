"""
Simple mail-list.

This script implements a simple "mail-list" tool.

It is monitoring a given mailbox, using imap, and maintains
a list of "subscribers". If a new mail is received, the tool
creates a new mail, using the sender data provided, and sends
this mail to all subscribers using SMTP.
"""

import argparse
import configparser
import json
import smtplib
import logging
import os
import sys
from os.path import exists
from time import sleep
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from imap_tools import MailBox, AND, MailMessageFlags
from dotenv import load_dotenv


class Attachment:
    """
    Attachment data type.

    Attachment is a internal data type to group
    the information for one attachment. It is used
    to transfer the attachments form IMAP to SMTP.
    """
    filename: str = None
    mimetype: str = "application/octet-stream"
    data: bytes = None


class Message:
    """
    Message data type.

    Message is a internal data type to group
    the information needed for a mail which shall be sent
    using SMTP. It is used for mail forwarding as well as
    replies.
    """
    sender_name: str = ""
    receivers: list[str] = []
    subject: str = ""
    text: str = ""
    html: str = ""
    attachments: list[Attachment] = []


class SubscriberCheckResult:
    """
    Data type for communication between Subscribers and Receiver.

    SubscriberCheckResult is a internal data type to group
    the information needed for handling a new message in the
    mailbox.
    """
    forward: bool = False
    receivers: list[str] = []
    unsubscribe_tag: str = '$>unsubscribe'


class Config:
    """
    Config groups all maillist configs and the parsing.
    """

    def __init__(self):
        self._get_args()
        self._get_config()
        self._get_secrets()

    def _get_args(self):
        """
        Get arguments from commandline, or defaults.
        """
        parser = argparse.ArgumentParser(description='Simple Maillist.')
        parser.add_argument('-c', '--config', default='./config', type=str,
                            help='configuration file')
        parser.add_argument('-m', '--maillist', default='./maillist.json', type=str,
                            help='maillist json file')
        parser.add_argument('-l', '--logfile', default='./maillist.log', type=str,
                            help='maillist logfile')
        parser.add_argument('-s', '--sleep', default='60', type=int,
                            help='sleep time between mail checks in seconds')
        parser.add_argument('-v', '--verbose', action="store_true",
                            help='print logs')
        parser.add_argument('-t', '--test', action="store_true",
                            help='send test mail on startup')
        parser.add_argument('-d', '--daemon', action="store_true",
                            help='run as daemon')
        parser.add_argument('-r', '--reduce_logs', action="store_true",
                            help='log only errors')

        args = parser.parse_args()

        log_level = logging.INFO
        if args.verbose:
            log_level = logging.DEBUG
        if args.reduce_logs:
            log_level = logging.ERROR
        logging.basicConfig(filename=args.logfile,
                            encoding='utf-8', level=log_level)

        if not args.reduce_logs:
            logging.getLogger().addHandler(logging.StreamHandler())

        if log_level == logging.DEBUG:
            logging.getLogger().setLevel(logging.DEBUG)
            logging.debug('verbose mode enabled')

        self.daemon = args.daemon
        logging.info('running as daemon: %r', self.daemon)

        self.sleep = args.sleep
        logging.info('sleep time set to %i seconds', self.sleep)

        self.config_file = args.config
        logging.debug('using config file %s', self.config_file)

        self.maillist_file = args.maillist
        logging.debug('using maillist file %s', self.maillist_file)

        self.send_test_mail = args.test
        logging.debug('send test mail: %r', self.send_test_mail)

    def _get_config(self):
        """
        Read config from config file.
        """

        if not exists(self.config_file):
            print('Config file %s doesn\'t exist!', self.config_file)
            logging.error('Config file %s doesn\'t exist!', self.config_file)
            sys.exit(1)

        config = configparser.ConfigParser()
        config.read(self.config_file)

        if 'mailbox' in config:
            mailbox = config['mailbox']
            self.mailbox_server = mailbox.get('server', None)
            self.mailbox_user = mailbox.get('user', None)
        else:
            self.mailbox_server = None
            self.mailbox_user = None

        logging.debug('mailbox server: %s', self.mailbox_server)
        logging.debug('mailbox user: %s', self.mailbox_user)

        if 'smtp' in config:
            smtp = config['smtp']
            self.smtp_server = smtp.get('server', None)
            self.smtp_user = smtp.get('user', None)
            self.smtp_port = smtp.get('port', '587')
            tls = smtp.get('tls', 'true')
            self.smtp_tls = tls.lower() == 'true'
        else:
            self.smtp_server = None
            self.smtp_user = None
            self.smtp_port = '587'
            self.smtp_tls = True

        logging.debug('smtp server: %s', self.smtp_server)
        logging.debug('smtp user: %s', self.smtp_user)
        logging.debug('smtp port: %s', self.smtp_port)
        logging.debug('use tls: %s', self.smtp_tls)

        if 'sender' in config:
            sender = config['sender']
            self.sender_address = sender.get('address', None)
            self.sender_name = sender.get('name', None)
        else:
            self.sender_address = None
            self.sender_name = None

        logging.debug('sender address: %s', self.sender_address)
        logging.debug('sender name: %s', self.sender_name)

        if 'test' in config:
            self.test_receiver = config['test'].get('receiver', None)
        else:
            self.test_receiver = None

        logging.debug('test receiver: %s', self.test_receiver)

        if 'snippets' in config:
            snippets = config['snippets']
            self.list_name = snippets.get('list_name', self.sender_address)
            self.subscribe_subject = snippets.get(
                'subscribe_subject', 'Welcome!')
            self.unsubscribe_subject = snippets.get(
                'unsubscribe_subject', 'Bye!')

            footer_text_file = snippets.get('footer_text', None)
            if footer_text_file is not None and exists(footer_text_file):
                with open(footer_text_file, 'r', encoding='utf-8') as f:
                    self.footer_text = f.read()
            else:
                self.footer_text = ""

            footer_html_file = snippets.get('footer_html', None)
            if footer_html_file is not None and exists(footer_html_file):
                with open(footer_html_file, 'r', encoding='utf-8') as f:
                    self.footer_html = f.read()
            else:
                self.footer_html = ""

            subscribe_text_file = snippets.get('footer_text', None)
            if subscribe_text_file is not None and exists(subscribe_text_file):
                with open(subscribe_text_file, 'r', encoding='utf-8') as f:
                    self.subscribe_text = f.read()
            else:
                self.subscribe_text = ""

            subscribe_html_file = snippets.get('footer_html', None)
            if subscribe_html_file is not None and exists(subscribe_html_file):
                with open(subscribe_html_file, 'r', encoding='utf-8') as f:
                    self.subscribe_html = f.read()
            else:
                self.subscribe_html = ""

            unsubscribe_text_file = snippets.get('footer_text', None)
            if unsubscribe_text_file is not None and exists(unsubscribe_text_file):
                with open(unsubscribe_text_file, 'r', encoding='utf-8') as f:
                    self.unsubscribe_text = f.read()
            else:
                self.unsubscribe_text = ""

            unsubscribe_html_file = snippets.get('footer_html', None)
            if unsubscribe_html_file is not None and exists(unsubscribe_html_file):
                with open(unsubscribe_html_file, 'r', encoding='utf-8') as f:
                    self.unsubscribe_html = f.read()
            else:
                self.unsubscribe_html = ""

        logging.debug('mail-list name: %s', self.list_name)
        logging.debug('footer text: %s', self.footer_text)
        logging.debug('footer html: %s', self.footer_html)
        logging.debug('subscribe subject: %s', self.subscribe_subject)
        logging.debug('subscribe text: %s', self.subscribe_text)
        logging.debug('subscribe html: %s', self.subscribe_html)
        logging.debug('unsubscribe subject: %s', self.unsubscribe_subject)
        logging.debug('unsubscribe text: %s', self.unsubscribe_text)
        logging.debug('unsubscribe html: %s', self.unsubscribe_html)

    def _get_secrets(self):
        """
        Read secrets from .env
        """
        load_dotenv()
        self.mailbox_password = os.environ.get('mailbox_password')
        if len(self.mailbox_password) == 0:
            logging.info('mailbox password is empty')

        self.smtp_password = os.environ.get('smtp_password')
        if len(self.smtp_password) == 0:
            logging.info('smtp password is empty')

    def check_config(self):
        """
        Assert that all mandatory config parameters are available.
        """
        assert self.mailbox_server is not None
        assert self.smtp_server is not None
        assert self.sender_address is not None
        if self.send_test_mail:
            assert self.test_receiver is not None
        if self.daemon:
            assert self.sleep > 0


class Sender:
    """
    The sender takes care of sending the mails.
    """

    def __init__(self, config: Config):
        self.config = config

    def send_mail(self, message: Message):
        """
        Send the given message.
        """
        # Use default sender name if none was provided
        if message.sender_name == "":
            if self.config.sender_name is not None:
                message.sender_name = self.config.sender_name
            else:
                message.sender_name = self.config.sender_address

        smtp_sender = f"{message.sender_name} <{self.config.sender_address}>"

        msg = MIMEMultipart()
        msg['Subject'] = message.subject
        msg['From'] = smtp_sender
        # Mention the sender address as receiver, all subscribers are BCC receivers
        msg['To'] = smtp_sender

        if len(message.html) > 0 and len(message.text) > 0:
            # Text and HTML -> alternative representations
            inner = MIMEMultipart('alternative')
            inner.attach(MIMEText(message.text, 'plain'))
            inner.attach(MIMEText(message.html, 'html'))
            msg.attach(inner)
        elif len(message.text) > 0:
            # Plain text message
            msg.attach(MIMEText(message.text, 'plain'))
        else:
            # HTML only message
            msg.attach(MIMEText(message.html, 'html'))

        for attachment in message.attachments:
            maintype, subtype = attachment.mimetype.split('/')
            part = MIMEBase(maintype, subtype)
            part.set_payload(attachment.data)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                            'attachment', filename=attachment.filename)
            msg.attach(part)

        sender = self.config.sender_address

        logging.debug('Sending message to %r', message.receivers)

        smtp = smtplib.SMTP(self.config.smtp_server,
                            port=self.config.smtp_port)
        if self.config.smtp_tls:
            smtp.starttls()
        if len(self.config.smtp_user) > 0:
            smtp.login(self.config.smtp_user,
                       self.config.smtp_password)
        smtp.sendmail(sender, message.receivers, msg.as_string())
        smtp.quit()


class Subscribers:
    """
    Subscribers manage the maillist subscribers.
    """

    def __init__(self, config: Config, sender: Sender):
        self.config = config
        self.sender = sender
        self._get_list()

    def _get_list(self):
        """
        Read maillist from JSON file.
        """
        if exists(self.config.maillist_file):
            with open(self.config.maillist_file, 'r', encoding='utf-8') as file:
                self._list = json.load(file)
        else:
            self._list = {'subscribers': []}
            self._save_list()

    def _save_list(self):
        """
        Save the maillist as JSON file.
        """
        with open(self.config.maillist_file, 'w', encoding='utf-8') as file:
            json.dump(self._list, file)

    def _get_key(self, tags: list[str] = None) -> str:
        """
        Get key calculates a unique key for the given tags.

        If the list is empty, the default key is 'subscribers'.
        """
        if tags is None:
            return 'subscribers'

        lower_tags = [tag.lower() for tag in tags]
        lower_tags.sort()
        return '__'.join(lower_tags)

    def _get_subscribers(self, tags: list[str] = None) -> list[str]:
        tag_subscribers = self._list.get(self._get_key(tags), [])
        full_subscribers = self._list.get('subscribers', [])
        subscribers = tag_subscribers + full_subscribers
        # remove duplicates
        return list(set(subscribers))

    def _is_allowed(self, sender: str, tags: list[str] = None) -> bool:
        subscribers = self._get_subscribers(tags)
        return sender in subscribers

    def _get_tags(self, subject: str) -> list[str]:
        tags = []
        for part in subject.strip().split(' '):
            part = part.strip()
            if part.startswith('#') and len(part) > 1:
                tag = part[1:]
                tags.append(tag)

        if len(tags) == 0:
            return None
        return tags

    def check(self, subject: str, sender: str) -> SubscriberCheckResult:
        """
        Check if mail is valid, process commands, and get
        all receivers for the given subject and sender.
        """
        tags = self._get_tags(subject)
        forward = self._handle_command(subject, sender, tags)

        if not forward:
            return SubscriberCheckResult()

        if self._is_allowed(sender, tags):
            receivers = self._get_subscribers(tags).copy()
            receivers.remove(sender)

            result = SubscriberCheckResult()
            result.receivers = receivers
            result.forward = True
            return result
        else:
            logging.warning(
                'sender %s tried to send %s, but is no subscriber', sender, subject)

    def _handle_command(self, subject: str, sender: str, tags: list[str] = None) -> bool:
        """
        Process subscribe and unsubscribe commands.
        """
        forward = True
        sub = subject.strip()
        if sub.startswith('$>'):
            # do not forward command messages
            forward = False
            command = sub[2:]
            if command.lower().startswith('subscribe'):
                self._add_subscriber(sender, tags)
            elif command.lower().startswith('unsubscribe'):
                self._remove_subscriber(sender, tags)

        return forward

    def _add_subscriber(self, address, tags: list[str] = None):
        """
        Add a new subscriber for the given tags.

        If tags are None, all messages are forwarded to the subscriber.
        """
        logging.info('New subscriber: %s', address)

        key = self._get_key(tags)
        if address not in self._list[key]:
            self._list[key].append(address)
            self._save_list()

        logging.info('new subscriber list for %r: %r', tags, self._list[key])

        message = Message()
        message.subject = self.config.subscribe_subject
        message.text = self.config.subscribe_text % {
            'list_name': self.config.list_name}
        message.text = self.config.subscribe_html % {
            'list_name': self.config.list_name}
        message.receivers = [address]

        self.sender.send_mail(message)

    def _remove_subscriber(self, address, tags: list[str] = None):
        """
        Remove a subscriber for the given tags.

        If tags are None, the subscriber is removed from the global list.
        """
        logging.info('User canceled subscription: %s', address)

        key = self._get_key(tags)
        if address in self._list[key]:
            self._list[key].remove(address)
            self._save_list()

        logging.info('new subscriber list for %r: %r', tags, self._list[key])

        message = Message()
        message.text = self.config.unsubscribe_text % {
            'list_name': self.config.list_name}
        message.text = self.config.unsubscribe_html % {
            'list_name': self.config.list_name}
        message.receivers = [address]

        self.sender.send_mail(message)


class Receiver:
    """
    The receiver takes care of checking for incoming messages.
    """

    def __init__(self, config: Config, subscribers: Subscribers, sender: Sender):
        self.config = config
        self.subscribers = subscribers
        self.sender = sender

    def process_mails(self):
        """
        Fetch and process all new mails.
        """
        logging.info("Processing new messages ...")

        with MailBox(self.config.mailbox_server).login(
                self.config.mailbox_user,
                self.config.mailbox_password) as mailbox:

            for msg in mailbox.fetch(criteria=AND(seen=False)):
                logging.debug('mark message %s as seen', msg.uid)

                mailbox.flag([msg.uid], [MailMessageFlags.SEEN], True)
                self._process_message(msg)

    def _process_message(self, msg):
        """
        Process a new message.
        """
        logging.info('Processing message %r', msg.uid)

        self._log_message(msg)

        subject = msg.subject
        result = self.subscribers.check(subject, msg.from_)
        if not result.forward:
            logging.debug('message shall be not forwarded')
            return

        if len(result.receivers) == 0:
            logging.info('no subscribers for %s', subject)
            return

        message = Message()
        message.subject = subject
        message.text = msg.text + self.config.footer_text
        message.html = msg.html + self.config.footer_html
        message.receivers += result.receivers
        message.sender_name = msg.from_values.name

        for att in msg.attachments:
            attachment = Attachment()
            attachment.filename = att.filename
            attachment.mimetype = att.content_type
            attachment.data = att.payload
            message.attachments.append(attachment)

        self.sender.send_mail(message)

    def _log_message(self, msg):
        """
        Log the given message
        """
        logging.info('From: %s', msg.from_)
        logging.debug('To: %s', msg.to)
        logging.info('Subject: %s', msg.subject)
        logging.debug('Flags: %s', msg.flags)
        logging.info('Sender name: %s', msg.from_values)
        if len(msg.text) > 0:
            logging.debug('Message Text:\n%s', msg.text)
        if len(msg.html) > 0:
            logging.debug('Message HTML:\n%s', msg.html)
        for att in msg.attachments:
            logging.debug('Attachment: %s %s', att.filename, att.content_type)


class Maillist:
    """
    Maillist receives mails and forwards it to subscribers.
    """

    def __init__(self, config: Config):
        """
        Create a new maillist.
        """
        self.config = config
        self.sender = Sender(self.config)
        self.subscribers = Subscribers(self.config, self.sender)
        self.receiver = Receiver(self.config, self.subscribers, self.sender)

        if self.config.send_test_mail:
            self._send_test_mail()

    def _send_test_mail(self):
        """
        Send a test message.
        """
        logging.info('Sending a test mail to %s', self.config.test_receiver)

        message = Message()
        message.receivers = [self.config.test_receiver]
        message.subject = "Maillist started!"
        message.text = "The maillist service was started!"

        self.sender.send_mail(message)

    def process_mails(self):
        """
        Receive message and forward to subscribers.
        """
        self.receiver.process_mails()

    def sleep(self):
        """
        Sleep until next check for new mails.
        """
        logging.info('Sleeping for %i seconds ...', self.config.sleep)
        sleep(self.config.sleep)


def main():
    """
    Run the maillist service.
    """
    config = Config()
    config.check_config()

    maillist = Maillist(config)

    if config.daemon:
        while True:
            maillist.process_mails()
            maillist.sleep()
    else:
        maillist.process_mails()


if __name__ == '__main__':
    main()
