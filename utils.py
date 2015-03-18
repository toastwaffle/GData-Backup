import getpass
import os
import sys

import gflags

import config_pb2

FLAGS = gflags.FLAGS

gflags.DEFINE_string('config_dir',
                     '~/.gdatabackup',
                     'Alternative location of the config_dir',
                     short_name='l')

def validate_config_dir(path):
    def resolve_path_validator(path):
        if os.path.isdir(path):
            return True

        try:
            os.mkdir(path)
            return True
        except OSError, e:
            return False

    try:
        resolve_path(path, resolve_path_validator)
        return True
    except utils.NonExistentPathError:
        return False

gflags.RegisterValidator('config_dir',
                         validate_config_dir,
                         message='--config_dir must be a directory')

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
    filepath = os.path.join(
        resolve_path(FLAGS.config_dir, os.path.isdir),
        "login.binproto"
    )

    login = config_pb2.Login()

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

def get_oauth_client_details():
    filepath = os.path.join(
        resolve_path(FLAGS.config_dir, os.path.isdir),
        "oauthclient.binproto"
    )

    client = config_pb2.OAuthClient()

    if filepath is not None and os.path.isfile(filepath):
        with open(filepath, 'r') as client_file:
            client.ParseFromString(client_file.read())
            return client
    else:
        print "Create an API client at https://console.developers.google.com"
        client.id = raw_input("Enter your client ID: ")
        client.secret = getpass.getpass("Enter your client secret: ")
        client.public_api_key = getpass.getpass("Enter your public API key: ")

        if filepath is not None:
            try:
                with open(filepath, 'w') as client_file:
                    client_file.write(client.SerializeToString())
            except IOError:
                sys.stderr.write(
                    'Could not save client credentials to {}\n'.format(filepath)
                )

        return client
