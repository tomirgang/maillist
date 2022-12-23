# Mail-list

This script implements a simple "mail-list" tool.

It is monitoring a given mailbox, using IMAP, and maintains
a list of "subscribers". If a new mail is received, the tool
creates a new mail, using the sender data provided, and sends
this mail to all subscribers using SMTP.

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
