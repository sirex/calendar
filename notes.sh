# Install dependencies
env/bin/pip install -r requirements.in


# Test calendar weekday names
LANG=lt_LT.UTF-8 python <<EOF
import calendar
print(list(calendar.day_name))
EOF


# Test dateutil rrule parser
env/bin/python <<EOF
import dateutil.rrule
import datetime
rule = dateutil.rrule.rrulestr(
    'RRULE:FREQ=YEARLY;INTERVAL=1;COUNT=5',
    dtstart=datetime.datetime(2020,1,1)
)
for x in rule:
    print(x)
EOF


# Test ical parser
env/bin/python <<EOF
from icalevents import icalevents
events = icalevents.events(file='Pagrindinis_sirexas@gmail.com.ics')
for ev in events:
    print(ev.start, ev.summary)
    print(ev.__dict__)
EOF

# Birth days of 10th powers of seconds
env/bin/python <<EOF
import dateutil.rrule
import datetime
rule = dateutil.rrule.rrulestr(
    'RRULE:FREQ=SECONDLY;INTERVAL=1000000000;COUNT=2',
    dtstart=datetime.datetime(1983,6,25)
)
for x in rule:
    print(x)
EOF


# 2020-02-03 17:59

env/bin/python gencal.py ~/Notes/calendar.txt 2019-12-30 -n 5
