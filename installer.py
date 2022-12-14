""" Installer for mail_list.

This scripts prepares interactive the environment for mail_list.py
"""

import os
import sys
import configparser
from prompt_toolkit import prompt


class Installer:
    """ Setup environment for mail_list. """

    footer_html = """
<hr>
<p>Dies eMail stammt von {list_name}.<br>
    Der Inhalt dieser Nachricht wurde von einem anderen Abonnenten erstellt und nicht überprüft.</p>
<p>Antworte mit dem Betreff <a href="mailto:{address}?subject=$>unsubscribe">$>unsubscribe</a> um keine weiteren eMails
    zu bekommen.</p>
<p>Antworte mit dem Betreff <a href="mailto:{address}?subject=$>unsubscribe {tags}">{tags}</a> um keine weiteren
    eMails für diesen Hashtag zu bekommen.</p>
"""

    footer_text = """
------

Dies eMail stammt von {list_name}.
Der Inhalt dieser Nachricht wurde von einem anderen Abonnenten erstellt und nicht überprüft.

Antworte mit dem Betreff '$>unsubscribe' um keine weiteren eMails zu bekommen.

Antworte mit dem Betreff '$>unsubscribe {tags}' um keine weiteren eMails für diesen Hashtag zu bekommen.
"""

    subscribe_html = """
<html>

<body>
    <h2>Hi!</h2>
    <p>Schön dass du da bist. Willkommen auf {list_name}.</p>
</body>

</html>
"""

    subscribe_text = """
Hi!

Schön dass du da bist. Willkommen auf {list_name}.
"""

    unsubscribe_html = """
<html>

<body>
    <h2>Hi!</h2>
    <p>Schade dass du gehst.</p>
    <p>Auf Wiedersehen,<br>{list_name}</p>
</body>

</html>
"""

    unsubscribe_text = """
Hi!

Schade dass du gehst.

Auf Wiedersehen,
{list_name}
"""
    data_path = None
    config = configparser.ConfigParser()

    def __init__(self):
        self.config['mailbox'] = {'server': '', 'user': ''}
        self.config['smtp'] = {'server': '', 'user': '',
                               'port': '587', 'tls': 'true'}
        self.config['sender'] = {'address': '', 'name': ''}
        self.config['test'] = {'receiver': ''}
        self.config['snippets'] = {'list_name': '',
                                   'footer_text': './data/snippets/footer.txt',
                                   'footer_html': './data/snippets/footer.html',
                                   'subscribe_text': './data/snippets/subscribe.txt',
                                   'subscribe_html': './data/snippets/subscribe.html',
                                   'subscribe_subject': 'Hello!',
                                   'unsubscribe_text': './data/snippets/unsubscribe.txt',
                                   'unsubscribe_html': './data/snippets/unsubscribe.html',
                                   'unsubscribe_subject': 'Bye!'}

    def _ask_data_dir(self):
        """ Ask for data dir. """
        self.data_path = prompt('Data location (default: ./data): ')
        if self.data_path.strip() == '':
            self.data_path = './data'

    def data_dir(self):
        """ Create data dir. """
        self._ask_data_dir()

        if not os.path.exists(self.data_path):
            create_dirs = False

            create = prompt('The path does not exist. Create it (Y/n)? ')
            if create.strip() == '':
                create = 'y'
            if create.strip().lower() == 'y':
                create_dirs = True

            if create_dirs:
                os.makedirs(self.data_path)

        if not os.path.exists(self.data_path):
            print('Path creation failed.')
            sys.exit(1)

    def mailbox(self):
        """ Collect information about the mailbox """
        imap_password = None
        smtp_password = None

        print('Mailbox data:')
        self.config['mailbox']['server'] = prompt('IMAP server: ')
        self.config['smtp']['server'] = prompt('SMTP server: ')

        login = prompt('Login required (Y/n)? ')
        if login.strip() == '':
            login = 'y'
        if login.strip().lower() == 'y':
            self.config['mailbox']['user'] = prompt('Username: ')
            imap_password = prompt('Password: ', is_password=True)

        smtp_login = prompt('SMTP login required (Y/n)? ')
        if smtp_login.strip() == '':
            smtp_login = 'y'
        if smtp_login.strip().lower() == 'y':
            same_login = prompt('Same login as IMAP (Y/n)? ')
            if same_login.strip() == '':
                same_login = 'y'
            if same_login.strip().lower() == 'y':
                self.config['smtp']['user'] = self.config['mailbox']['user']
                smtp_password = imap_password
            else:
                self.config['smtp']['user'] = prompt('Username: ')
                smtp_password = prompt('Password: ', is_password=True)

        if imap_password is not None or smtp_password is not None:
            content = ''
            if imap_password is not None:
                content += f'mailbox_password = {imap_password}\n'
            if smtp_password is not None:
                content += f'smtp_password = {smtp_password}\n'
            with open(os.path.join(self.data_path, '.env'), 'w', encoding='utf-8') as f:
                f.write(content)
                f.flush()

        print('Sender data:')
        self.config['sender']['address'] = prompt('Sender address: ')
        self.config['sender']['name'] = prompt('Sender name: ')
        self.config['test']['receiver'] = prompt('Testmail receiver address: ')

    def snippets(self):
        """ Generate default snippets. """

        print('Snippets:')
        self.config['snippets']['list_name'] = prompt('List name: ')
        self.config['snippets']['subscribe_subject'] = prompt(
            'Subscribe subject: ')
        self.config['snippets']['unsubscribe_subject'] = prompt(
            'Unsubscribe subject: ')

        with open(os.path.join(self.data_path, 'config'), 'w', encoding='utf-8') as f:
            self.config.write(f)

        create = prompt('Create snippet templates in data dir (Y/n)? ')
        if create.strip() == '':
            create = 'y'
        if create.strip().lower() == 'y':
            snippets_path = os.path.join(self.data_path, 'snippets')
            os.makedirs(snippets_path)
            with open(os.path.join(snippets_path, 'footer.html'), 'w', encoding='utf-8') as f:
                f.write(self.footer_html)
                f.flush()

            with open(os.path.join(snippets_path, 'footer.txt'), 'w', encoding='utf-8') as f:
                f.write(self.footer_text)
                f.flush()

            with open(os.path.join(snippets_path, 'subscribe.html'), 'w', encoding='utf-8') as f:
                f.write(self.subscribe_html)
                f.flush()

            with open(os.path.join(snippets_path, 'subscribe.txt'), 'w', encoding='utf-8') as f:
                f.write(self.subscribe_text)
                f.flush()

            with open(os.path.join(snippets_path, 'unsubscribe.html'), 'w', encoding='utf-8') as f:
                f.write(self.unsubscribe_html)
                f.flush()

            with open(os.path.join(snippets_path, 'unsubscribe.txt'), 'w', encoding='utf-8') as f:
                f.write(self.unsubscribe_text)
                f.flush()

    def setup(self):
        """ Generate mail_list config data. """
        self.data_dir()
        self.mailbox()
        self.snippets()


if __name__ == '__main__':
    if os.path.exists('./data/config'):
        sys.exit(0)

    Installer().setup()
