#!/usr/bin/env python2
"""Script to retrieve and back up calendars and contacts from Google."""

import datetime
import httplib2
import os
import sys

from apiclient import discovery
from gdata import gauth
from gdata.contacts import client as contacts_client
from oauth2client import client as oauth_client
from oauth2client import file as oauth_file
import gflags

import calendar_pb2
import contacts_pb2
import flags  # pylint: disable=unused-import
import utils


FLAGS = gflags.FLAGS


class GdataBackup(object):
    """Encapsulating class for script."""

    def __init__(self):
        self._flow = None
        self._oauth_token = None
        self._storage = oauth_file.Storage(
            os.path.join(
                utils.resolve_path(FLAGS.config_dir),
                "credentials.dat"
            )
        )
        self._credentials = self._storage.get()

    @property
    def flow(self):
        """Get the OAuth flow object."""
        if self._flow is None:
            self._flow = oauth_client.flow_from_clientsecrets(
                os.path.join(
                    utils.resolve_path(FLAGS.config_dir),
                    "client_secrets.json"
                ),
                scope=[
                    "https://www.google.com/m8/feeds",
                    "https://www.googleapis.com/auth/calendar"
                ],
                redirect_uri="urn:ietf:wg:oauth:2.0:oob"
            )
            self._flow.user_agent = self.__class__.__name__

        return self._flow

    @property
    def credentials(self):
        """Get the OAuth credentials object used for the calendar client."""
        if self._credentials is None or self._credentials.invalid == True:
            auth_uri = self.flow.step1_get_authorize_url()

            utils.output((
                "Please visit {0} in your browser to authorise the app. Once "
                "authorised, return here and enter the provided auth code.\n\n"
            ).format(auth_uri), 0)

            auth_code = raw_input("Enter the auth code: ")

            self._credentials = self.flow.step2_exchange(auth_code)

            self._storage.locked_put(self._credentials)

        return self._credentials

    @property
    def oauth_token(self):
        """Get the OAuth token object used for the contacts client."""
        if self._oauth_token is None:
            self._oauth_token = gauth.OAuth2Token(
                self.flow.client_id,
                self.flow.client_secret,
                self.flow.scope,
                self.flow.user_agent,
                self.flow.auth_uri,
                self.flow.token_uri,
                self.credentials.access_token,
                self.credentials.refresh_token,
                self.flow.revoke_uri
            )

        return self._oauth_token

    def contacts(self):
        """Download and save all contacts."""
        client = contacts_client.ContactsClient(
            auth_token=self.oauth_token,
            source="GData-Backup"
        )

        feed = client.GetContacts()

        utils.output("Starting contacts backup.\n", 1)

        contact_list_pb = contacts_pb2.ContactList()

        count = 0

        while feed is not None:
            for contact in feed.entry:
                utils.contact_to_protobuf(contact, contact_list_pb)
                count += 1
                utils.output("\rBacked up {0} contacts".format(count), 2)

            next_uri = feed.GetNextLink()

            if next_uri:
                feed = client.GetContacts(uri=next_uri.href)
            else:
                feed = None

        # Add newline after the counter stops counting
        utils.output("\n", 2)

        contact_filename = os.path.join(
            utils.resolve_path(FLAGS.storage_dir),
            "contacts-{0}.binproto".format(
                datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
            )
        )

        with open(contact_filename, "w+") as contact_file:
            contact_file.write(contact_list_pb.SerializeToString())

        utils.output("Finished contacts backup.\n", 1)

    def calendar(self):
        """Download and save all calendars and events."""
        service = discovery.build(
            "calendar",
            "v3",
            http=self.credentials.authorize(httplib2.Http())
        )

        utils.output("Starting calendar backup.\n", 1)

        calendar_list = calendar_pb2.CalendarList()

        page_token = None
        while True:
            calendars = service.calendarList().list(
                pageToken=page_token
            ).execute()

            for calendar in calendars["items"]:
                if calendar["accessRole"] == "owner":
                    utils.output(
                        "Backing up {0}\n".format(calendar["summary"]),
                        2
                    )

                    calendar_pb = calendar_list.calendar.add()
                    calendar_pb.summary = calendar["summary"]
                    calendar_pb.timezone = calendar["timeZone"]
                    try:
                        calendar_pb.description = calendar["description"]
                    except KeyError:
                        pass
                    try:
                        calendar_pb.location = calendar["location"]
                    except KeyError:
                        pass

                    count = 0

                    event_page_token = None
                    first_request = True
                    while True:
                        events = service.events().list(
                            calendarId=calendar["id"],
                            pageToken=event_page_token,
                            singleEvents=True
                        ).execute()

                        if first_request:
                            first_request = False
                            try:
                                for reminder in events["default_reminders"]:
                                    calendar_pb.default_reminder.add(
                                        method=reminder["method"],
                                        minutes=reminder["minutes"]
                                    )
                            except KeyError:
                                pass

                        for event in events["items"]:
                            utils.event_to_protobuf(event, calendar_pb)
                            count += 1
                            utils.output(
                                "\rBacked up {0} events".format(count),
                                2
                            )

                        event_page_token = events.get("nextPageToken")
                        if not event_page_token:
                            break

                    # Add newline after the counter stops counting
                    utils.output("\n", 2)

            page_token = calendars.get("nextPageToken")
            if not page_token:
                break

        calendar_filename = os.path.join(
            utils.resolve_path(FLAGS.storage_dir),
            "calendar-{0}.binproto".format(
                datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
            )
        )

        with open(calendar_filename, "w+") as calendar_file:
            calendar_file.write(calendar_list.SerializeToString())

        utils.output("Finished calendar backup.\n", 1)


def main(argv):
    """Load the flag values, and run the backup routines."""
    try:
        argv = FLAGS(argv)
    except gflags.FlagsError as exc:
        sys.stderr.write(
            "{0}\nUsage: {1} ARGS\n{2}".format(exc, sys.argv[0], FLAGS)
        )
        sys.exit(1)

    backup = GdataBackup()

    if FLAGS.calendar:
        backup.calendar()

    if FLAGS.contacts:
        backup.contacts()


if __name__ == "__main__":
    main(sys.argv)
