"""Definition of the various flags."""

import gflags

gflags.DEFINE_string("storage_dir",
                     None,
                     "Directory to store backups in",
                     short_name="d")
gflags.MarkFlagAsRequired("storage_dir")

gflags.DEFINE_bool("contacts",
                   False,
                   "Whether to backup contacts",
                   short_name="c")

gflags.DEFINE_bool("calendar",
                   False,
                   "Whether to backup calendar",
                   short_name="a")

gflags.DEFINE_string('config_dir',
                     '~/.gdatabackup',
                     'Alternative location of the config_dir',
                     short_name='l')

gflags.DEFINE_integer('verbosity',
                      1,
                      'How much information to output',
                      short_name='v',
                      lower_bound=0,
                      upper_bound=2)
