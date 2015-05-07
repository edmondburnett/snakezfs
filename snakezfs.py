#!/usr/bin/python

import time
import sys
import fcntl
import errno
import argparse
import subprocess


LOCK_PATH = "/tmp/snakezfs.lock"

class ArgParser(argparse.ArgumentParser):

    """ Override default behaviour of argparse errors """
    def error(self, message):
        sys.stderr.write('ERROR: %s\n' % message)
        self.print_help()
        sys.exit(2)


def create_snapshot(timestamp, pool):
    """ Create a new local snapshot """
    options = "%s@backup_%s" % (pool, timestamp)
    process_snapshot = subprocess.Popen(
        ['zfs', 'snapshot', options], stdout=subprocess.PIPE)
    out, err = process_snapshot.communicate()


def send_backup(timestamp, pool, fsname, user, hostname, incremental, netcat, prev):
    """ Send the snapshot to the remote server """
    if incremental:
        if netcat:
            command = "zfs send -i %s %s@backup_%s | nc -w 30 %s 8023" % (
                prev, pool, timestamp, hostname)
        else:
            command = "zfs send -i %s %s@backup_%s | ssh %s@%s zfs recv -F %s/%s" % (
                prev, pool, timestamp, user, hostname, pool, fsname)
    else:
        if netcat:
            command = "zfs send %s@backup_%s | nc %s 8023" % (
                pool, timestamp, hostname)
        else:
            command = "zfs send %s@backup_%s | ssh %s@%s zfs recv %s/%s" % (
                pool, timestamp, user, hostname, pool, fsname)
    subprocess.call(command, shell=True)


def remove_snapshots(previous, num):
    """ Purge excess snapshots from source system.

        previous: a list of snapshot names
        num: int of the max number of snapshots to retain
    """
    if len(previous) > num:
        last_index = len(previous) - num
        to_remove = previous[:last_index]
        for snapshot in to_remove:
            subprocess.call(['zfs', 'destroy', snapshot])


def main():
    # handle command line arguments
    parser = ArgParser()
    parser.add_argument("pool", help="name of ZFS pool")
    parser.add_argument("fsname", help="name of remote file system")
    parser.add_argument("user", help="username for backup server SSH login")
    parser.add_argument(
        "hostname", help="hostname or IP address of remote backup server")
    parser.add_argument(
        "-i", "--incremental", help="perform an incremental backup", action="store_true")
    parser.add_argument(
        "-n", "--netcat", help="send using netcat (trusted networks only, must open target connection manually)", action="store_true")
    parser.add_argument(
        "-l", "--lock", help="allow only one instance of snakezfs to be running at the same point of time", action="store_true")
    args = parser.parse_args()

    # print help if no arguments specified
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    if args.lock:
        lock_file = open(LOCK_PATH, 'w')
        try:
            fcntl.lockf(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError as e:
            if e.errno == errno.EACCES or e.errno == errno.EAGAIN:
                sys.stderr.write("Another instance is already running.")
                sys.exit(3)

    timestamp = time.strftime("%m-%d-%Y_%H:%M")
    prev = None
    previous = []

    # get the last snapshot name (if incremental)
    if args.incremental:
        snapshot_list = subprocess.check_output(
            'zfs list -o name -t snapshot | grep @backup_', shell=True).split('\n')
        previous = filter(None, snapshot_list)
        prev = previous[-1]

    # remove old snapshots
    remove_snapshots(previous, 7)

    # create a new snapshot
    create_snapshot(timestamp, args.pool)

    # send snapshot to backup server
    send_backup(timestamp, args.pool, args.fsname, args.user,
                args.hostname, args.incremental, args.netcat, prev)


if __name__ == '__main__':
    main()
