import datetime
import httplib2
import os
import sys

import gflags

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run

import calendar_pb2
import utils

FLAGS = gflags.FLAGS

def get_service():
    client = utils.get_oauth_client_details()

    FLOW = OAuth2WebServerFlow(
        client_id=client.id,
        client_secret=client.secret,
        scope='https://www.googleapis.com/auth/calendar',
        user_agent='GData-Backup'
    )

    storage = Storage(os.path.join(
        utils.resolve_path(FLAGS.config_dir, os.path.isdir),
        'calendar-credentials.dat'
    ))
    credentials = storage.get()

    if credentials is None or credentials.invalid == True:
        credentials = run(FLOW, storage)

    http = httplib2.Http()
    http = credentials.authorize(http)

    return build(serviceName='calendar', version='v3', http=http,
                 developerKey=client.public_api_key)

def convert_calendar_entry_to_protobuf(entry, calendar):
    event = calendar.event.add()

    try:
        event.summary = entry['summary']
    except KeyError:
        pass

    try:
        event.description = entry['description']
    except KeyError:
        pass

    try:
        event.location = entry['location']
    except KeyError:
        pass

    try:
        event.start = entry['start']['date']
    except KeyError:
        pass

    try:
        event.start = entry['start']['dateTime']
    except KeyError:
        pass

    try:
        event.start_timezone = entry['start']['timeZone']
    except KeyError:
        pass

    if 'endTimeUnspecified' in entry and not entry['endTimeUnspecified']:
        try:
            event.end = entry['end']['date']
        except KeyError:
            pass

        try:
            event.end = entry['end']['dateTime']
        except KeyError:
            pass

        try:
            event.end_timezone = entry['end']['timeZone']
        except KeyError:
            pass

    event.use_default_reminder = entry['reminders']['useDefault']

    try:
        for reminder_entry in entry['reminders']['overrides']:
            reminder = event.reminder.add()
            reminder.method = reminder_entry['method']
            reminder.minutes = reminder_entry['minutes']
    except KeyError:
        pass

def do_backup(storage_dir):
    service = get_service()

    calendar_list = calendar_pb2.CalendarList()

    page_token = None
    while True:
        calendars = service.calendarList().list(pageToken=page_token).execute()

        for calendar in calendars['items']:
            if calendar['accessRole'] == 'owner':
                print 'Backing up {}'.format(calendar['summary'])

                cal = calendar_list.calendar.add()
                cal.summary = calendar['summary']
                cal.timezone = calendar['timeZone']
                try:
                    cal.description = calendar['description']
                except KeyError:
                    pass
                try:
                    cal.location = calendar['location']
                except KeyError:
                    pass

                count = 0

                event_page_token = None
                first_request = True
                while True:
                    events = service.events().list(calendarId=calendar['id'], pageToken=event_page_token, singleEvents=True).execute()

                    if first_request:
                        first_request = False
                        try:
                            for entry in events['default_reminders']:
                                reminder = cal.default_reminder.add()
                                reminder.method = entry['method']
                                reminder.minutes = entry['minutes']
                        except KeyError:
                            pass

                    for event in events['items']:
                        convert_calendar_entry_to_protobuf(event, cal)
                        count += 1
                        sys.stdout.write('\rBacked up {} events'.format(count))

                    event_page_token = events.get('nextPageToken')
                    if not event_page_token:
                        break

                print '' # Add newline after the counter stops counting

        page_token = calendars.get('nextPageToken')
        if not page_token:
            break

    calendar_filename = os.path.join(
        utils.resolve_path(storage_dir, os.path.isdir),
        "calendar-{}.binproto".format(
            datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        )
    )

    with open(calendar_filename, 'w+') as calendar_file:
        calendar_file.write(calendar_list.SerializeToString())
