What is SnakeZFS
================
SnakeZFS is a simple Python script for performing ZFS snapshot and send/receive 
operations. It was built to meet a specific need of a client.

The typical use case is to run with a cron job at regular intervals, sending
the backup(s) to a remote server via SSH.

Compatibility
=============
Interfaces with standard ZFS and bash commands, so it should work on most Linux 
and Solaris-based operating systems. Developed and tested on Debian, Archlinux, 
and OpenIndiana.

Usage
=====
The user account that runs the script must have an SSH public key added
to the remote server's ~/.ssh/authorized\_keys file. Test the login first by
SSH'ing into the remote server. If this is the first login, you will need to
accept the prompt for adding the server to your list of known hosts.

`ssh <username>@<hostname>`

Create a snapshot and perform a full backup:

`./snakezfs.py <pool name> <username> <hostname>`

Create a snapshot and perform an incremental backup:

`./snakezfs.py -i <pool name> <username> <hostname>`
