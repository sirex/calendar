# Install dependencies
sudo pacman -S ttf-ubuntu-font-family
poetry install



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

env/bin/python gencal.py ~/notes/calendar.txt 2019-12-30 -n 5


# 2020-05-23 05:09

env/bin/python gencal.py ~/notes/calendar.txt 2020-05-18 -n 5


# 2020-05-23 06:01 Trying to fix moon phases

env/bin/python <<EOF
import astral, datetime
a = astral.Astral()
phase = a.moon_phase(date=datetime.datetime(2020, 5, 22, 5), rtype=float)
print(phase)
EOF

env/bin/python <<EOF
import datetime
today = datetime.date.today()
print(datetime.datetime(today.year, today.month, today.day))
print(datetime.datetime.combine(today, datetime.datetime.max.time()))
print(datetime.datetime(today.year, today.month, today.day) + datetime.timedelta(1))
EOF

env/bin/pip install pyephem

env/bin/python <<EOF
import datetime
import ephem
import astral
date = ephem.Date(datetime.date(2020, 5, 22))
newmoon = ephem.next_new_moon(date).datetime()
print(newmoon)
a = astral.Astral()
phase = a.moon_phase(date=newmoon, rtype=float)
print(phase)
EOF

env/bin/python <<EOF
import datetime
import ephem
import astral
date = datetime.date(2020, 5, 22)
phase = ephem.Moon(ephem.Date(date)).phase
print(phase)
a = astral.Astral()
phase = a.moon_phase(date=date, rtype=float)
phase = 28 - phase if phase > 14 else phase
print(phase / 14 * 100)
EOF

env/bin/pip install matplotlib

env/bin/python

import datetime
import ephem
import astral
import matplotlib.pyplot as plt
x = [datetime.datetime(2020, 5, 22) + datetime.timedelta(hours=i*6) for i in range(30*4*2)]
a = astral.Astral()
a = [a.moon_phase(date=d, rtype=float) for d in x]
a = [(28 - p if p > 14 else p) / 14 * 100 for p in a]
e = [ephem.Moon(ephem.Date(d)).phase for d in x]
fig, ax = plt.subplots()
ax.plot(x, a, label="Astral")
ax.plot(x, e, label="Ephem")
ax.legend()
plt.show()


moon = ephem.Moon(ephem.Date(datetime.datetime(2020, 5, 22)))
moon.moon_phase

d = datetime.datetime(2020, 5, 22)
d = ephem.Date(d)
pnm = ephem.previous_new_moon(d)
nnm = ephem.next_new_moon(d)
(d - pnm) / (nnm - pnm) * 8
d - pnm
nnm - pnm


env/bin/pip install pytz

env/bin/python

import datetime
import pytz

d = datetime.date(2020, 5, 22)
tz = pytz.timezone('Europe/Vilnius')
d.astimezone(datetime.timezone.utc)
d.astimezone(tz)

d.astimezone(tz).utcoffset()


env/bin/python <<EOF
import pytz
import datetime
import ephem

def day_to_moon_phase_code(day):
    tz = pytz.timezone('Europe/Vilnius')
    day = datetime.datetime(day.year, day.month, day.day)
    utcoffset = day.astimezone(tz).utcoffset()
    day = datetime.datetime(day.year, day.month, day.day)
    day = day - utcoffset
    day = ephem.Date(day)

    phases = [
        (0, ephem.next_new_moon(day)),
        (2, ephem.next_first_quarter_moon(day)),
        (4, ephem.next_full_moon(day)),
        (6, ephem.next_last_quarter_moon(day)),
    ]

    phase, date = min(phases, key=lambda x: x[1])

    if date - day > 1:
        return phase - 1 if phase else 7
    else:
        return phase

print(day_to_moon_phase_code(datetime.date(2020, 5, 21)))
print(day_to_moon_phase_code(datetime.date(2020, 5, 22)))
print(day_to_moon_phase_code(datetime.date(2020, 5, 23)))
EOF


# pdfunite can be used to merge all pages into one pdf file
pdfunite print/*.pdf calendar.pdf


# 2022-06-29 10:58 Migrate to Poetry

poetry init -n --name "wcal" --description "Personalized printable wall calendar generator." --license "AGPL"
# wcal stands for Wall Calendar
poetry add astral pyephem python-dateutil icalevents pytz

# 2022-06-29 11:04 Generate new calendar sheets

poetry run python gencal.py ~/notes/calendar.txt 2022-07-11 -n 12
poetry run python gencal.py ~/notes/calendar.txt 2022-07-11 -n 1

# Inkscape does not support unicode emoji symbols
inkscape --help
inkscape --export-type=PNG --export-overwrite --export-dpi=300 output/2022-07-11.svg

# By default ImageMagic also does not support unicode emoji symbols
convert -units pixelsperinch -density 300 "output/*.svg" print/calendar.pdf

# Final working version:
rm output/*.{svg,png}
poetry run python gencal.py ~/notes/calendar.txt 2022-07-11 -n 13
for f in output/*.svg; do
    rsvg-convert --dpi-x=600 --dpi-y=600 -o ${f%.*}.png $f
done
convert -units pixelsperinch -density 600 -quality 100 "output/*.png" print/calendar.pdf


