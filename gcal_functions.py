from gcsa.google_calendar import GoogleCalendar
from gcsa.calendar import Calendar
import time
from datetime import datetime, timedelta

GC = GoogleCalendar(credentials_path="/home/jasmine/PROJECTS/hornsync/credentials.json")

# fetches events from an individual calendar
def _get_calendar_events(gcal_id, start=None, end=None): 

    events = []

    for event in GC.get_events(calendar_id=gcal_id, 
                               time_min=start,
                               time_max=end): 
        events.append(event)

    return events

def combine_events(org_names, gcal_ids): 

    EVENTS = []

    for (i, gcal_id), selected_club in zip(enumerate(gcal_ids), org_names):
        for event in _get_calendar_events(gcal_id):
            event.color_id = i 
            event.summary = f"[{selected_club}] - {event.summary}"
            EVENTS.append(event)
    
    return EVENTS

def consolidate_calendar(EVENTS, org_names):

    consolidated_cal = Calendar("Your Hornsync Clubs", 
                                description=f"**Events for your selected clubs via Hornsync**\n\nSelected Clubs: {', '.join(org_names)}")
    consolidated_cal = GC.add_calendar(consolidated_cal)
    
    for event in EVENTS: 
        GC.import_event(event, calendar_id=consolidated_cal.id)

    return consolidated_cal

def get_gcal_embed(gcal_id):
    #embed_url = f"https://calendar.google.com/calendar/embed?src={gcal_id}"
    # iframe_code = f'<iframe src="{embed_url}" style="border: 0" width="800" height="600" frameborder="0" scrolling="no"></iframe>'
    iframe_code = f'<p align="center"><iframe src="https://calendar.google.com/calendar/embed?src={gcal_id}&ctz=America%2FChicago" style="border-width:0" width="1200" height="650" frameborder="0" scrolling="no"></iframe></p?'

    return iframe_code