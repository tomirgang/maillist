# Maillist

This script implements a simple "maillist" tool.

It is monitoring a given mailbox, using IMAP, and maintains
a list of "subscribers". If a new mail is received, the tool
creates a new mail, using the sender data provided, and sends
this mail to all subscribers using SMTP.

## Usage

Users of the maillist are eMail addresses, there are no user
accounts or web-UIs. The tool support two commands, `$>subscribe`
and `$>unsubscribe` and hash-tags for content filtering.

A user can subscribe for the full list by sending a mail with
subject `$>subscribe` to the monitored mailbox. Then the tool
will add the user to the list and send a welcome mail, using
the templates from the snippets folder and the subject form the
configuration file. These replies should contain the information
how to cancel the subscription.

To integrate the maillist into your project documentation, you can
create simple `mailto` link:

- Subscribe: `<a href="mailto:<your@mailbox.addr>?subject=$>subscribe&body=I want to get updates!">subscribe</a>`
- Cancel subscription: `<a href="mailto:<your@mailbox.addr>?subject=$>unsubscribe&body=I don't want to get updates anymore!">subscribe</a>`

A user who subscribed to the list can also send messages to the list.
This is a communication tool, and no marketing tool. A message send
form the user to the mailbox will be picked up by the tool, extended
with a given footer snippet, and forwarded to all other subscribers,
using the display name of the sender, and the sender address configured,
usually the address of the monitored mailbox.

### Hash-Tags

For more fine-grained subscriptions, the maillist allows using hash-tags, also for
subscription. A user can subscribe for a specific topic, e.g. `#updates`:

- Subscribe for `#updates`: `<a href="mailto:<your@mailbox.addr>?subject=$>subscribe #updates&body=I want to get updates!">subscribe</a>`
- Cancel subscription for `#updates`: `<a href="mailto:<your@mailbox.addr>?subject=$>unsubscribe #updates&body=I don't want to get updates anymore!">subscribe</a>`

A user who subscribed for updates is allowed to send mails to the list, using the tag `#updates`,
but the user is not allowed to send mails for a wider scope. For more details see next section.

### Hash-Tag scopes

For sending, hash-tag scopes work in an additive way. A user who has subscribed to `#updates` is
allowed to send mails to more specific scopes, e.g. `#updates #project`.

For receiving it's the other way around. Mails are forwarded to subscribers of a larger scope, e.g.
a mail send to `#updates #project` will be forwarded to all subscribers without any hash-tag, and all
subscribers of `#updates`, `#project` and `#updates #project`, but not to subscribers of 
`#updates #project #other_tag`.

## Setup

You can run the `installer.py` to generate the required configuration and templates.

## Run the maillist

With reduced logs in daemon mode:

```bash
python maillist.py -d -r
```

With extended logs for debugging and testing:

```bash
python maillist.py -d -v
```

## Docker

### Build the image

```bash
docker build -t maillist .
```

### Generate the configuration

```bash
docker run -it --rm  -v <path or volume>:/usr/src/app/data maillist:latest python installer.py
```

### Run the maillist

```bash
docker run -d --name maillist -v /home/tom/git/maillist/dockerdata:/usr/src/app/data maillist:latest python maillist.py -d -r
```
