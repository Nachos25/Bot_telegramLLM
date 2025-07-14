from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from config import GOOGLE_CREDENTIALS_FILE, CALENDAR_ID

SCOPES = ['https://www.googleapis.com/auth/calendar']

credentials = service_account.Credentials.from_service_account_file(
    GOOGLE_CREDENTIALS_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=credentials)


def list_free_slots(start_iso, end_iso, duration_minutes):
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start_iso,
        timeMax=end_iso,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    # Найти свободные интервалы между событиями
    free_slots = []
    start = datetime.fromisoformat(start_iso)
    end = datetime.fromisoformat(end_iso)
    busy = [
        (
            datetime.fromisoformat(e['start']['dateTime']),
            datetime.fromisoformat(e['end']['dateTime'])
        ) for e in events if 'dateTime' in e['start']
    ]
    current = start
    while current + timedelta(minutes=duration_minutes) <= end:
        slot_end = current + timedelta(minutes=duration_minutes)
        overlap = any(b[0] < slot_end and b[1] > current for b in busy)
        if not overlap:
            free_slots.append((current, slot_end))
        current += timedelta(minutes=15)
    return free_slots


def create_appointment(
    specialist, start_iso, end_iso, summary, description, attendee_email=None
):
    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_iso, 'timeZone': 'Europe/Kiev'},
        'end': {'dateTime': end_iso, 'timeZone': 'Europe/Kiev'},
        'attendees': [{'email': attendee_email}] if attendee_email else [],
        'transparency': 'opaque',
        'status': 'confirmed',
    }
    created_event = service.events().insert(
        calendarId=CALENDAR_ID, body=event
    ).execute()
    return created_event 