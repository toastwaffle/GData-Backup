import getpass
import os

import gflags

import login_pb2

FLAGS = gflags.FLAGS

gflags.DEFINE_string('login_file',
                     '~/.gdatabackup-login',
                     'Alternative location of the credentials file',
                     short_name='l')

class Error(Exception):
    pass

class NonExistentPathError(Error):
    pass

def resolve_path(path, validator):
    if validator(path):
        return path

    if path.startswith('~'):
        if validator(os.path.expanduser(path)):
            return os.path.expanduser(path)
        else:
            raise NonExistentPathError("Could not resolve path")

    if validator(os.path.realpath(path)):
        return os.path.realpath(path)

    raise NonExistentPathError("Could not resolve path")

def get_login_details():
    def login_filepath_validator(path):
        return os.path.isdir(os.path.split(path)[0]) and not os.path.isdir(path)

    try:
        filepath = resolve_path(FLAGS.login_file,
                                login_filepath_validator)
    except NonExistentPathError:
        sys.stderr.write(
            (
                'Invalid login file path, will not save login credentials: {}\n'
            ).format(FLAGS.login_file)
        )
        filepath = None

    login = login_pb2.Login()

    if filepath is not None and os.path.isfile(filepath):
        with open(filepath, 'r') as login_file:
            login.ParseFromString(login_file.read())
            return login
    else:
        login.email = raw_input("Enter your email address: ")
        login.password = getpass.getpass("Enter your password: ")

        if filepath is not None:
            try:
                with open(filepath, 'w') as login_file:
                    login_file.write(login.SerializeToString())
            except IOError:
                sys.stderr.write(
                    'Could not save login credentials to {}\n'.format(filepath)
                )

        return login
