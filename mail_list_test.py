"""
Tests for mail-list.
"""

import logging
import os
import pytest
from mail_list import Config, Maillist, main


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
            assert config.subscribe_text == text, "subscribe text"

        with open('./snippets/subscribe.html', 'r', encoding='utf-8') as file:
            text = file.read()
            assert config.subscribe_html == text, "subscribe html"

        with open('./snippets/unsubscribe.txt', 'r', encoding='utf-8') as file:
            text = file.read()
            assert config.unsubscribe_text == text, "unsubscribe text"

        with open('./snippets/unsubscribe.html', 'r', encoding='utf-8') as file:
            text = file.read()
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


class TestSubscribers:
    """ Test for mail_list.Subscribers. """


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
