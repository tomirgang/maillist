""" Installer for mail_list.

This scripts prepares interactive the environment for mail_list.py
"""

import os
import sys
from prompt_toolkit import prompt


footer_html = """
<hr>
<p>This mail is originating from {list_name}.<br>
    The content above was created by another subscriber and not reviewed.</p>
<p>To unsubscribe to all tags, reply to this mail with subject <a
        href="mailto:{address}?subject=$>unsubscribe">$>unsubscribe</a>.</p>
<p>To unsubscribe to this tag, reply to this mail with subject <a
        href="mailto:{address}?subject={unsubscribe_tag}">{unsubscribe_tag}</a>.</p>

<hr>
<p>Dies eMail stammt von {list_name}.<br>
    Der Inhalt dieser Nachricht wurde von einem anderen Abonnenten erstellt und nicht überprüft.</p>
<p>Antworte mit dem Betreff <a href="mailto:{address}?subject=$>unsubscribe">$>unsubscribe</a> um keine weiteren eMails
    zu bekommen.</p>
<p>Antworte mit dem Betreff <a href="mailto:{address}?subject={unsubscribe_tag}">{unsubscribe_tag}</a> um keine weiteren
    eMails für diesen Hashtag zu bekommen.</p>
"""

footer_text = """
------

This mail is originating from {list_name}.
The content above was created by another subscriber and not reviewed.

To unsubscribe to all tags, reply to this mail with subject '$>unsubscribe'.

To unsubscribe to this tag, reply to this mail with subject '{unsubscribe_tag}'.

---

Dies eMail stammt von {list_name}.
Der Inhalt dieser Nachricht wurde von einem anderen Abonnenten erstellt und nicht überprüft.

Antworte mit dem Betreff '$>unsubscribe' um keine weiteren eMails zu bekommen.

Antworte mit dem Betreff '{unsubscribe_tag}' um keine weiteren eMails für diesen Hashtag zu bekommen.
"""

subscribe_html = """
<html>

<body>
    <h2>Hi!</h2>
    <p>Nice that you joined. Welcome at {list_name}.</p>

    <hr>

    <h2>Hi!</h2>
    <p>Schön dass du da bist. Wilkommen auf {list_name}.</p>
</body>

</html>
"""

subscribe_text = """
Hi!

Nice that you joined. Welcome at {list_name}.

---

Hi!

Schön dass du da bist. Wilkommen auf {list_name}.
"""

unsubscribe_html = """
<html>

<body>
    <h2>Hi!</h2>
    <p>Sorry that you leave.</p>
    <p>Goodbye,<br>{list_name}</p>

    <hr>

    <h2>Hi!</h2>
    <p>Schade dass du gehst.</p>
    <p>Auf Wiedersehen,<br>{list_name}</p>
</body>

</html>
"""

unsubscribe_text = """
Hi!

Sorry that you leave.

Goodbye,
{list_name}

---

Hi!

Schade dass du gehst.

Auf Wiedersehen,
{list_name}
"""

def _data_dir():
    # get data directory path
    path = prompt('Data location (default: ./data): ')
    if path.strip() == '':
        path = './data'
    if not os.path.exists(path):
        create = prompt('The path does not exist. Create it (Y/n)? ')
        if create.strip() == '':
            create = 'y'
        if not create.strip().lower() == 'y':
            sys.exit(1)
        os.makedirs(path)
        if not os.path.exists(path):
            print('Path creation failed.')
            sys.exit(1)



if __name__ == '__main__':
    _data_dir()


