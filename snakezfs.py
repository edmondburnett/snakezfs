#!/usr/bin/python

import time
import sys
import argparse
import subprocess


class ArgParser(argparse.ArgumentParser):
    """ Override default behaviour of argparse errors """
    def error(self, message):
        sys.stderr.write('ERROR: %s\n' % message)
        self.print_help()
        sys.exit(2)


def create_snapshot(timestamp, pool, filesystem):
    # create filesystem, ignore if already exists
    devnull = open('/dev/null', 'w')
    subprocess.Popen(['zfs', 'create', pool + '/' + filesystem],
            stdout=devnull, stderr=devnull)

    # add a new snapshot
    options = "%s/%s@%s" % (pool, filesystem, timestamp)
    process_snapshot = subprocess.Popen(['zfs', 'snapshot', options], stdout=subprocess.PIPE)
    out,err = process_snapshot.communicate()


def send_backup(timestamp, pool, filesystem, user, hostname, incremental):
    if incremental:
        command = "zfs send %s/%s@%s | zfs recv -F %s/testback" % (pool, filesystem, timestamp, pool)
    else:
        command = "zfs send -i %s/%s@%s | zfs recv -F %s/testback" % (pool, filesystem, timestamp, pool)

    subprocess.call(command, shell=True)



def main():
    # handle command line arguments
    parser = ArgParser()

    #parser.add_argument("-c", "--create", help="Create new ZFS snapshot", action="store_true")
    #parser.add_argument("-s", "--send", help="Send ZFS snapshot", action="store_true")
    parser.add_argument("pool", help="name of ZFS pool")
    parser.add_argument("fsname", help="name of ZFS backup file system")
    parser.add_argument("user", help="username for backup server SSH login")
    parser.add_argument("hostname", help="hostname or IP address of remote backup server")
    parser.add_argument("-i", "--incremental", help="perform an incremental backup", action="store_true")
    args = parser.parse_args()

    # print help if no arguments specified
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    timestamp = time.strftime("%m-%d-%Y_%H:%M")

    print args.incremental

    create_snapshot(timestamp, args.pool, args.fsname)
    send_backup(timestamp, args.pool, args.fsname, args.user, args.hostname, args.incremental)



if __name__ == '__main__':
    main()
