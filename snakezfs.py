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


def create_snapshot(timestamp, pool):
    """ Create a new local snapshot """
    options = "%s@backup_%s" % (pool, timestamp)
    process_snapshot = subprocess.Popen(['zfs', 'snapshot', options], stdout=subprocess.PIPE)
    out,err = process_snapshot.communicate()


def send_backup(timestamp, pool, fsname, user, hostname, incremental, prev):
    """ Send the snapshot to the remote server """
    if incremental:
        command = "zfs send -i %s %s@backup_%s | ssh %s@%s zfs recv -F %s/%s" % (prev, pool, timestamp, user, hostname, pool, fsname)
    else:
        command = "zfs send %s@backup_%s | ssh %s@%s zfs recv %s/%s" % (pool, timestamp, user, hostname, pool, fsname)
    subprocess.call(command, shell=True)


def main():
    # handle command line arguments
    parser = ArgParser()
    parser.add_argument("pool", help="name of ZFS pool")
    parser.add_argument("fsname", help="name of remote file system")
    parser.add_argument("user", help="username for backup server SSH login")
    parser.add_argument("hostname", help="hostname or IP address of remote backup server")
    parser.add_argument("-i", "--incremental", help="perform an incremental backup", action="store_true")
    args = parser.parse_args()

    # print help if no arguments specified
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    timestamp = time.strftime("%m-%d-%Y_%H:%M")

    # get the last snapshot name (if incremental)
    prev = None
    if args.incremental:
        snapshot_list = subprocess.check_output('zfs list -o name -t snapshot | grep @backup_', shell=True).split('\n')
        previous = filter(None, snapshot_list)
        print 'num of snapshots: ', len(previous)
        print previous
        prev = previous[-1]

    # create a new snapshot
    create_snapshot(timestamp, args.pool)

    # send snapshot to backup server
    send_backup(timestamp, args.pool, args.fsname, args.user, args.hostname, args.incremental, prev)


if __name__ == '__main__':
    main()
