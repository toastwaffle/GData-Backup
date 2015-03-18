#!/usr/bin/env python2

import getpass
import os
import sys

import gflags

import calendar_backup
import contacts_backup
import utils

FLAGS = gflags.FLAGS

gflags.DEFINE_string('storage_dir',
                     None,
                     'Directory to store backups in',
                     short_name='d')
gflags.MarkFlagAsRequired('storage_dir')

gflags.DEFINE_bool('contacts',
                   False,
                   'Whether to backup contacts',
                   short_name='c')

gflags.DEFINE_bool('calendar',
                   False,
                   'Whether to backup calendar',
                   short_name='a')

def validate_storage_dir(path):
    try:
        utils.resolve_path(path, os.path.isdir)
        return True
    except utils.NonExistentPathError:
        return False


gflags.RegisterValidator('storage_dir',
                         validate_storage_dir,
                         message='--storage_dir must be a directory')

def main(argv):
    try:
        argv = FLAGS(argv)  # parse flags
    except gflags.FlagsError, e:
        print '{0}\nUsage: {1} ARGS\n{2}'.format(e, sys.argv[0], FLAGS)
        sys.exit(1)

    if FLAGS.calendar:
        print 'Backing up calendar'
        calendar_backup.do_backup(FLAGS.storage_dir)
        print 'Finished backing up calendar'

    if FLAGS.contacts:
        print 'Backing up contacts'
        contacts_backup.do_backup(FLAGS.storage_dir)
        print 'Finished backing up contacts'

if __name__ == '__main__':
    main(sys.argv)
