"""Utility functions for backing up contacts and calendars."""

import os
import sys

import gflags
import pathlib

import contacts_pb2


FLAGS = gflags.FLAGS


def resolve_path(path):
    """Ensure that a directory exists.

    Args:
        path: (str) A path to a directory, optionally relative or including the
            ~ home directory expansion.

    Raises:
        OSError: If path is nonsensical or cannot be created.
    """
    path_obj = pathlib.Path(os.path.expanduser(path))

    try:
        return str(path_obj.resolve())
    except OSError as _:
        os.mkdir(str(path_obj))
        return str(path_obj.resolve())


def output(message, level=0):
    """Output a message to the console at a given verbosity level.

    Args:
        message: (str) The message to output. Will not automatically insert a
            new line.
        level: (int) Verbosity level to output at. Higher numbers are more
            likely to be hidden.
    """
    if level <= FLAGS.verbosity:
        sys.stdout.write(message)


def contact_to_protobuf(contact, contact_list_pb):  # pylint: disable=too-many-branches
    """Convert a contact from the Google API to our protobuf type.

    Args:
        contact: (object) Contact object returned from the Google API.
        contact_list_pb: (contacts_pb2.ContactList) Contact list to add the
            contact to.
    """
    contact_pb = contact_list_pb.contact.add()

    if contact.name is not None:
        if contact.name.full_name is not None:
            contact_pb.name = contact.name.full_name.text
        else:
            name_parts = []

            if contact.name.name_prefix is not None:
                name_parts.append(contact.name.name_prefix.text)

            if contact.name.given_name is not None:
                name_parts.append(contact.name.given_name.text)

            if contact.name.additional_name is not None:
                name_parts.append(contact.name.additional_name.text)

            if contact.name.family_name is not None:
                name_parts.append(contact.name.family_name.text)

            if contact.name.name_suffix is not None:
                name_parts.append(contact.name.name_suffix.text)

            contact_pb.name = " ".join(name_parts)
    elif contact.title.text is not None:
        contact_pb.name = contact.title.text

    for email in contact.email:
        email_pb = contact_pb.email.add()

        email_pb.address = email.address
        email_pb.primary = (email.primary == 'true')

        if email.label is not None:
            email_pb.label = email.label

        try:
            email_pb.type = contacts_pb2.Type.Value(email.rel[33:].upper())
        except AttributeError:
            email_pb.type = contacts_pb2.UNKNOWN
        except TypeError:
            email_pb.type = contacts_pb2.UNKNOWN

    for phone in contact.phone_number:
        phone_pb = contact_pb.phone.add()

        phone_pb.number = phone.text
        phone_pb.primary = (phone.primary == 'true')

        if phone.label is not None:
            phone_pb.label = phone.label

        try:
            phone_pb.type = contacts_pb2.Type.Value(phone.rel[33:].upper())
        except AttributeError:
            phone_pb.type = contacts_pb2.Type.UNKNOWN
        except TypeError:
            phone_pb.type = contacts_pb2.UNKNOWN


def event_to_protobuf(event, calendar_pb):
    """Convert an event from the Google API to our protobuf type.

    Args:
        event: (object) Event object returned from the Google API.
        calendar_pb: (calendar_pb2.Calendar) Calendar to add the
            event to.
    """
    event_pb = calendar_pb.event.add()

    try:
        event_pb.summary = event['summary']
    except KeyError:
        pass

    try:
        event_pb.description = event['description']
    except KeyError:
        pass

    try:
        event_pb.location = event['location']
    except KeyError:
        pass

    try:
        event_pb.start = event['start']['date']
    except KeyError:
        pass

    try:
        event_pb.start = event['start']['dateTime']
    except KeyError:
        pass

    try:
        event_pb.start_timezone = event['start']['timeZone']
    except KeyError:
        pass

    if 'endTimeUnspecified' in event and not event['endTimeUnspecified']:
        try:
            event_pb.end = event['end']['date']
        except KeyError:
            pass

        try:
            event_pb.end = event['end']['dateTime']
        except KeyError:
            pass

        try:
            event_pb.end_timezone = event['end']['timeZone']
        except KeyError:
            pass

    event_pb.use_default_reminder = event['reminders']['useDefault']

    try:
        for reminder in event['reminders']['overrides']:
            event_pb.reminder.add(
                method=reminder['method'],
                minutes=reminder['minutes']
            )
    except KeyError:
        pass
