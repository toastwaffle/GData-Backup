import datetime
import os
import sys

import gdata.contacts.client
import gdata.contacts.data
import gflags

import contacts_pb2
import utils

FLAGS = gflags.FLAGS

def convert_contact_entry_to_protobuf(entry, contact_list):
    contact = contact_list.contact.add()

    if entry.name is not None:
        if entry.name.full_name is not None:
            contact.name = entry.name.full_name.text
        else:
            name_parts = []

            if entry.name.name_prefix is not None:
                name_parts.append(entry.name.name_prefix.text)

            if entry.name.given_name is not None:
                name_parts.append(entry.name.given_name.text)

            if entry.name.additional_name is not None:
                name_parts.append(entry.name.additional_name.text)

            if entry.name.family_name is not None:
                name_parts.append(entry.name.family_name.text)

            if entry.name.name_suffix is not None:
                name_parts.append(entry.name.name_suffix.text)

            contact.name = " ".join(name_parts)
    elif entry.title.text is not None:
        contact.name = entry.title.text

    for e in entry.email:
        email = contact.email.add()

        email.address = e.address
        email.primary = (e.primary == 'true')

        if e.label is not None:
            email.label = e.label

        try:
            email.type = contacts_pb2.Type.Value(e.rel[33:].upper())
        except AttributeError:
            email.type = contacts_pb2.UNKNOWN
        except TypeError:
            email.type = contacts_pb2.UNKNOWN

    for p in entry.phone_number:
        phone = contact.phone.add()

        phone.number = p.text
        phone.primary = (p.primary == 'true')

        if p.label is not None:
            phone.label = p.label

        try:
            phone.type = contacts_pb2.Type.Value(p.rel[33:].upper())
        except AttributeError:
            phone.type = contacts_pb2.Type.UNKNOWN
        except TypeError:
            phone.type = contacts_pb2.UNKNOWN

def do_backup(storage_dir):
    client = gdata.contacts.client.ContactsClient(
        source='GData-Backup'
    )

    login = utils.get_login_details()

    client.ClientLogin(login.email, login.password, client.source)

    feed = client.GetContacts()

    contact_list = contacts_pb2.ContactList()

    count = 0

    while feed is not None:
        for entry in feed.entry:
            convert_contact_entry_to_protobuf(entry, contact_list)
            count += 1
            utils.quiet_print('\rBacked up {} contacts'.format(count))

        next_uri = feed.GetNextLink()

        if next_uri:
            feed = client.GetContacts(uri=next_uri.href)
        else:
            feed = None

    utils.quiet_print('\n') # Add newline after the counter stops counting

    contact_filename = os.path.join(
        utils.resolve_path(storage_dir, os.path.isdir),
        "contacts-{}.binproto".format(
            datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        )
    )

    with open(contact_filename, 'w+') as contact_file:
        contact_file.write(contact_list.SerializeToString())
