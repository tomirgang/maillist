"""
Tests for mail-list.
"""

import logging
import os
import base64
import pytest
from mail_list import Config, Maillist, main, Sender, Message, Attachment, Subscribers


class ArgsDummy:
    """ Replacement for argparser return value. """
    logfile: str = './maillist.log'
    daemon: bool = False
    sleep: int = 60
    config: str = './config'
    maillist: str = './maillist.json'
    test: bool = False
    verbose: bool = False
    reduce_logs: bool = False


class TestConfig:
    """ Test for mail_list.Config. """
    config: dict = {'mailbox': {'server': 'imappro.zoho.eu', 'user': 'info@360tasks.de'},
                    'smtp': {'server': 'smtppro.zoho.eu', 'user': 'info@360tasks.de', 'port': '587',
                             'tls': 'true'},
                    'sender': {'address': 'info@360tasks.de', 'name': 'Tom'},
                    'test': {'receiver': 'thomas@irgang.eu'},
                    'snippets': {'list_name': 'info@360tasks.de',
                                 'footer_text': './snippets/footer.txt',
                                 'footer_html': './snippets/footer.html',
                                 'subscribe_text': './snippets/subscribe.txt',
                                 'subscribe_html': './snippets/subscribe.html',
                                 'subscribe_subject': 'Welcome!',
                                 'unsubscribe_text': './snippets/unsubscribe.txt',
                                 'unsubscribe_html': './snippets/unsubscribe.html',
                                 'unsubscribe_subject': 'Bye!'}}

    def _patch_args(self, mocker, args):
        mocker.patch("mail_list.Config._interface_argparse",
                     return_value=args)

    def test_get_args_loglevel(self, mocker):
        """ Test default log level. """
        self._patch_args(mocker, ArgsDummy())
        Config()
        assert logging.getLogger().level == logging.INFO

    def test_get_args_loglevel_verbose(self, mocker):
        """ Test verbose log level. """
        args = ArgsDummy()
        args.verbose = True
        self._patch_args(mocker, args)
        Config()
        assert logging.getLogger().level == logging.DEBUG

    def test_get_args_loglevel_reduced(self, mocker):
        """ Test reduced log level. """
        args = ArgsDummy()
        args.reduce_logs = True
        self._patch_args(mocker, args)
        Config()
        assert logging.getLogger().level == logging.ERROR

    def test_get_args_no_daemon(self, mocker):
        """ Test daemon mode, daemon off. """
        args = ArgsDummy()
        args.daemon = False
        self._patch_args(mocker, args)
        config = Config()
        assert config.daemon is False

    def test_get_args_daemon(self, mocker):
        """ Test daemon mode, daemon on. """
        args = ArgsDummy()
        args.daemon = True
        self._patch_args(mocker, args)
        config = Config()
        assert config.daemon is True

    def test_get_args_sleep(self, mocker):
        """ Test sleep time. """
        args = ArgsDummy()
        args.sleep = 123
        self._patch_args(mocker, args)
        config = Config()
        assert config.sleep == 123

    def test_get_args_config_file(self, mocker):
        """ Test config file argument. """
        args = ArgsDummy()
        self._patch_args(mocker, args)
        config = Config()
        assert config.config_file is './config'

    def test_get_args_mail_list_file(self, mocker):
        """ Test mail-list file argument. """
        args = ArgsDummy()
        self._patch_args(mocker, args)
        config = Config()
        assert config.maillist_file is './maillist.json'

    def test_get_args_test(self, mocker):
        """ Test sleep time. """
        args = ArgsDummy()
        args.test = True
        self._patch_args(mocker, args)
        config = Config()
        assert config.send_test_mail is True

    def _patch_config(self, mocker, config):
        mocker.patch("mail_list.Config._interface_configparser",
                     return_value=config)
        mocker.patch("mail_list.Config._interface_argparse",
                     return_value=ArgsDummy())

    def test_get_config_mailbox(self, mocker):
        """ Test mailbox config options. """
        self._patch_config(mocker, self.config)
        config = Config()
        assert config.mailbox_server is 'imappro.zoho.eu'
        assert config.mailbox_user is 'info@360tasks.de'

    def test_get_config_no_mailbox(self, mocker):
        """ Test mailbox config options defaults. """
        config = self.config.copy()
        del config['mailbox']
        self._patch_config(mocker, config)
        config = Config()
        assert config.mailbox_server is None
        assert config.mailbox_user is None

    def test_get_config_smtp(self, mocker):
        """ Test smtp config options. """
        self._patch_config(mocker, self.config)
        config = Config()
        assert config.smtp_server is 'smtppro.zoho.eu'
        assert config.smtp_port is '587'
        assert config.smtp_user is 'info@360tasks.de'
        assert config.smtp_tls is True

    def test_get_config_no_smtp(self, mocker):
        """ Test smtp config options defaults. """
        config = self.config.copy()
        del config['smtp']
        self._patch_config(mocker, config)
        config = Config()
        assert config.smtp_server is None
        assert config.smtp_port is '587'
        assert config.smtp_user is None
        assert config.smtp_tls is True

    def test_get_config_sender(self, mocker):
        """ Test sender config options. """
        self._patch_config(mocker, self.config)
        config = Config()
        assert config.sender_name is 'Tom'
        assert config.sender_address is 'info@360tasks.de'

    def test_get_config_no_sender(self, mocker):
        """ Test sender config options defaults. """
        config = self.config.copy()
        del config['sender']
        self._patch_config(mocker, config)
        config = Config()
        assert config.sender_name is None
        assert config.sender_address is None

    def test_get_config_test(self, mocker):
        """ Test test config options. """
        self._patch_config(mocker, self.config)
        config = Config()
        assert config.test_receiver is 'thomas@irgang.eu'

    def test_get_config_no_test(self, mocker):
        """ Test test config options defaults. """
        config = self.config.copy()
        del config['test']
        self._patch_config(mocker, config)
        config = Config()
        assert config.test_receiver is None

    def test_get_config_snippets(self, mocker):
        """ Test snippets config options. """
        self._patch_config(mocker, self.config)
        config = Config()
        assert config.list_name == 'info@360tasks.de'
        assert config.subscribe_subject == 'Welcome!'
        assert config.unsubscribe_subject == 'Bye!'

        with open('./snippets/footer.txt', 'r', encoding='utf-8') as file:
            text = file.read()
            assert config.footer_text == text, "footer text"

        with open('./snippets/footer.html', 'r', encoding='utf-8') as file:
            text = file.read()
            assert config.footer_html == text, "footer html"

        with open('./snippets/subscribe.txt', 'r', encoding='utf-8') as file:
            text = file.read()
            text = text.format(list_name=config.list_name)
            assert config.subscribe_text == text, "subscribe text"

        with open('./snippets/subscribe.html', 'r', encoding='utf-8') as file:
            text = file.read()
            text = text.format(list_name=config.list_name)
            assert config.subscribe_html == text, "subscribe html"

        with open('./snippets/unsubscribe.txt', 'r', encoding='utf-8') as file:
            text = file.read()
            text = text.format(list_name=config.list_name)
            assert config.unsubscribe_text == text, "unsubscribe text"

        with open('./snippets/unsubscribe.html', 'r', encoding='utf-8') as file:
            text = file.read()
            text = text.format(list_name=config.list_name)
            assert config.unsubscribe_html == text, "subscribe html"

    def test_get_config_no_snippets(self, mocker):
        """ Test snippets config options defaults. """
        config = self.config.copy()
        del config['snippets']
        self._patch_config(mocker, config)
        config = Config()
        assert config.list_name == 'info@360tasks.de'
        assert config.footer_text == ''
        assert config.footer_html == ''
        assert config.subscribe_subject == 'Welcome!'
        assert config.subscribe_text == ''
        assert config.subscribe_html == ''
        assert config.unsubscribe_subject == 'Bye!'
        assert config.unsubscribe_text == ''
        assert config.unsubscribe_html == ''

    def _patch_defaults(self, mocker):
        """ Get default config object. """
        mocker.patch("mail_list.Config._interface_configparser",
                     return_value=self.config)
        mocker.patch("mail_list.Config._interface_argparse",
                     return_value=ArgsDummy())

    def test_get_secrets(self, mocker):
        """ Test loading secrets from env. """
        self._patch_defaults(mocker)
        mocker.patch("dotenv.load_dotenv")
        os.environ['mailbox_password'] = 'testpassword123'
        os.environ['smtp_password'] = 'testpassword456'
        config = Config()
        assert config.mailbox_password == 'testpassword123'
        assert config.smtp_password == 'testpassword456'

    def test_check_config_mailbox_server(self, mocker):
        """ Test that check config detects issues - mailbox_server. """
        self._patch_defaults(mocker)
        config = Config()
        config.mailbox_server = None
        with pytest.raises(AssertionError):
            config.check_config()

    def test_check_config_smtp_server(self, mocker):
        """ Test that check config detects issues - smtp_server. """
        self._patch_defaults(mocker)
        config = Config()
        config.smtp_server = None
        with pytest.raises(AssertionError):
            config.check_config()

    def test_check_config_sender_address(self, mocker):
        """ Test that check config detects issues - sender_address. """
        self._patch_defaults(mocker)
        config = Config()
        config.sender_address = None
        with pytest.raises(AssertionError):
            config.check_config()

    def test_check_config_test_receiver(self, mocker):
        """ Test that check config detects issues - test_receiver. """
        self._patch_defaults(mocker)
        config = Config()
        config.test_receiver = None
        config.send_test_mail = True
        with pytest.raises(AssertionError):
            config.check_config()

    def test_check_config_sleep(self, mocker):
        """ Test that check config detects issues - sleep. """
        self._patch_defaults(mocker)
        config = Config()
        config.sleep = 0
        config.daemon = True
        with pytest.raises(AssertionError):
            config.check_config()


class TestSender:
    """ Test for mail_list.Sender. """

    def _get_config(self, mocker):
        """ Get default config object. """
        mocker.patch("mail_list.Config._interface_configparser",
                     return_value=TestConfig.config)
        mocker.patch("mail_list.Config._interface_argparse",
                     return_value=ArgsDummy())

        return Config()

    def test_send_mail_html(self, mocker):
        """ Test for mail content. """
        mocker.patch("mail_list.Sender._interface_smtplib")
        config = self._get_config(mocker)

        sender = Sender(config)

        message = Message()
        message.html = "HTML"
        message.text = "TEXT"
        message.receivers = ['test@exmple.com']
        message.sender_name = 'SENDER'
        message.subject = 'SUBJECT'

        sender.send_mail(message)

        sender._interface_smtplib.assert_called_once()

        args = Sender._interface_smtplib.call_args.args
        assert args[0] == config.sender_address
        assert args[1] == message.receivers
        assert message.sender_name in args[2]
        assert message.subject in args[2]
        assert message.html in args[2]
        assert message.text in args[2]

    def test_send_mail_sender_config(self, mocker):
        """ Test for fallback to config sender name. """
        mocker.patch("mail_list.Sender._interface_smtplib")
        config = self._get_config(mocker)
        sender = Sender(config)

        message = Message()

        sender.send_mail(message)

        sender._interface_smtplib.assert_called_once()

        args = Sender._interface_smtplib.call_args.args
        assert config.sender_name in args[2]

    def test_send_mail_sender_address_fallback(self, mocker):
        """ Test for fallback to sender address as sender name. """
        mocker.patch("mail_list.Sender._interface_smtplib")
        config = self._get_config(mocker)
        sender = Sender(config)

        message = Message()

        config.sender_name = None

        sender.send_mail(message)

        sender._interface_smtplib.assert_called_once()

        args = Sender._interface_smtplib.call_args.args
        assert f'{config.sender_address} <{config.sender_address}>' in args[2]

    def test_send_mail_attachment(self, mocker):
        """ Test for sending mails with attachments. """
        mocker.patch("mail_list.Sender._interface_smtplib")
        config = self._get_config(mocker)
        sender = Sender(config)

        attachment = Attachment()
        attachment.filename = 'hello.txt'
        attachment.mimetype = 'application/octet-stream'
        attachment.data = 'Hello, World!'.encode(encoding='utf-8')
        message = Message()
        message.attachments = [attachment]

        config.sender_name = None

        sender.send_mail(message)

        sender._interface_smtplib.assert_called_once()

        args = Sender._interface_smtplib.call_args.args
        assert attachment.filename in args[2]
        assert base64.b64encode(attachment.data).decode(
            encoding='utf-8') in args[2]


class TestSubscribers:
    """ Test for mail_list.Subscribers. """

    def _get_config(self, mocker):
        """ Get default config. """
        mocker.patch("mail_list.Config._interface_configparser",
                     return_value=TestConfig.config)
        mocker.patch("mail_list.Config._interface_argparse",
                     return_value=ArgsDummy())

        return Config()

    def _get_sender(self, mocker, config):
        """ Get default sender. """
        mocker.patch("mail_list.Sender._interface_smtplib")

        return Sender(config=config)

    def _get_subscribers(self, mocker):
        """ Get default subscriber. """
        mocker.patch("mail_list.Subscribers._save_list")
        self.config = self._get_config(mocker)
        self.sender = self._get_sender(mocker, self.config)
        self.config.maillist_file = 'NO_FILE'
        return Subscribers(self.config, self.sender)

    def test_get_list(self, mocker):
        """ Test for fallback data structure. """
        subscribers = self._get_subscribers(mocker)

        assert subscribers._list == {'subscribers': []}

    def test_get_key(self, mocker):
        """ Test for key generation form tags. """
        subscribers = self._get_subscribers(mocker)

        tags = ['test', 'one', 'two']
        assert subscribers._get_key(tags) == 'one#test#two'

        assert subscribers._get_key() == 'subscribers'

    def test_get_subscribers(self, mocker):
        """ Test for receiver list calculation.  """
        subscribers = self._get_subscribers(mocker)
        subscribers._list['subscribers'] = ['full@subscriber.de']
        subscribers._list['test'] = ['test@subscriber.de']
        subscribers._list['a#test'] = ['a_test@subscriber.de']
        subscribers._list['b#test'] = ['b_test@subscriber.de']
        subscribers._list['a#b#test'] = ['a_b_test@subscriber.de']

        receivers = subscribers._get_subscribers()
        assert receivers == ['full@subscriber.de'], 'no tags'

        tags = ['test']
        receivers = subscribers._get_subscribers(tags)
        assert set(receivers) == set(['full@subscriber.de',
                                      'test@subscriber.de',
                                      'a_test@subscriber.de',
                                      'b_test@subscriber.de',
                                      'a_b_test@subscriber.de']), 'test'

        tags = ['a', 'b']
        receivers = subscribers._get_subscribers(tags)
        assert set(receivers) == set(['full@subscriber.de',
                                      'a_b_test@subscriber.de']), 'a, b'

        tags = ['b', 'test']
        receivers = subscribers._get_subscribers(tags)
        assert set(receivers) == set(['full@subscriber.de',
                                      'b_test@subscriber.de',
                                      'a_b_test@subscriber.de']), 'b, test'

    def test_is_allowed(self, mocker):
        """ Test for allowed senders.  """
        subscribers = self._get_subscribers(mocker)
        subscribers._list['subscribers'] = ['full@subscriber.de']
        subscribers._list['test'] = ['test@subscriber.de']
        subscribers._list['a#test'] = ['a_test@subscriber.de']
        subscribers._list['b#test'] = ['b_test@subscriber.de']
        subscribers._list['a#b#test'] = ['a_b_test@subscriber.de']

        tags = ['test']
        allowed = subscribers._is_allowed('b_test@subscriber.de', tags)
        assert allowed is False, 'broader audience'

        tags = ['test', 'b']
        allowed = subscribers._is_allowed('b_test@subscriber.de', tags)
        assert allowed is True, 'fitting audience'

        tags = ['test', 'b', 'a']
        allowed = subscribers._is_allowed('b_test@subscriber.de', tags)
        assert allowed is True, 'smaller audience'

        tags = ['test', 'b', 'a']
        allowed = subscribers._is_allowed('no@subscriber.de', tags)
        assert allowed is False, 'no subscriber'

    def test_get_tags(self, mocker):
        """ Test for tag extraction. """
        subscribers = self._get_subscribers(mocker)

        subject = "Re: Fwd: Hallo #test #a#b # asdf #d welt"
        tags = subscribers._get_tags(subject)
        assert set(tags) == set(['test', 'a', 'b', 'd'])

        subject = "Re: Fwd: Hallo # asdf welt"
        tags = subscribers._get_tags(subject)
        assert tags is None


class TestReceiver:
    """ Test for mail_list.Receiver. """


class TestMaillist:
    """ Test for mail_list.Maillist. """


def test_main(mocker):
    """ Test for mail_list.main. """
    mocker.patch("mail_list.Config._interface_configparser",
                 return_value=TestConfig.config)
    mocker.patch("mail_list.Config._interface_argparse",
                 return_value=ArgsDummy())
    mocker.patch('mail_list.Config.check_config')
    mocker.patch('mail_list.Maillist.process_mails')

    main()

    Config.check_config.assert_called_once()
    Maillist.process_mails.assert_called_once()
