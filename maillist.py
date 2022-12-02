"""
Simple maillist.
"""

import argparse
import configparser
import glob
import os
import json
from imap_tools import MailBox, AND, MailMessageFlags


def get_args():
    """
    Get arguments from commandline, or defaults.
    """
    parser = argparse.ArgumentParser(description='Simple Maillist.')
    parser.add_argument('-c', '--config', default='./config',
                        help='configuration file')
    parser.add_argument('-d', '--data', default='.',
                        help='folder for list files')

    args = parser.parse_args()

    return args


def get_config(args):
    """
    Read config from configfile.
    """
    config = configparser.ConfigParser()
    config.read(args.config)

    return config


def get_lists(args):
    """
    Read all maillists from data directory.
    """
    pattern = os.path.join(args.data, '*.json')
    list_files = glob.glob(pattern)

    lists = {}
    for list_file in list_files:
        with open(list_file, encoding='utf-8') as f:
            lists[list_file] = json.load(f)

    return lists


def save_list(file, maillist):
    """
    Save the given maillist as JSON file.
    """
    with open(file, encoding='utf-8') as f:
        json.dump(f, maillist)


def fetch_mails(config):
    with MailBox(config['mailbox']['server']).login(
            config['mailbox']['user'],
            config['mailbox']['password']) as mailbox:

        for msg in mailbox.fetch(criteria=AND(seen=False)):
            mailbox.flag([msg.uid], [MailMessageFlags.SEEN], True)
            process_message(msg)


def process_message(msg):
    print(msg.to, msg.from_, msg.subject, msg.flags)


def main():
    args = get_args()
    config = get_config(args)
    lists = get_lists(args)

    fetch_mails(config)


if __name__ == '__main__':
    main()
