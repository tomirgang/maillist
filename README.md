# Mail-list

This script implements a simple "mail-list" tool.

It is monitoring a given mailbox, using IMAP, and maintains
a list of "subscribers". If a new mail is received, the tool
creates a new mail, using the sender data provided, and sends
this mail to all subscribers using SMTP.
