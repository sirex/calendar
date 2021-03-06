import argparse
import calendar
import collections
import datetime
import pathlib

import astral
import astral.sun
import ephem
import dateutil.parser
import dateutil.rrule
import pytz


class Box:

    def __init__(self, p=None, x=0, y=0, w=0, h=0):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.l = p.l + x if p else x  # noqa
        self.r = p.l + x + w if p else x + w
        self.t = p.t + y if p else y
        self.b = p.t + y + h if p else y + h

    def shrink(
        self,
        h=None,  # horizontally
        v=None,  # vertically
    ):
        v = v or h
        return Box(
            self,
            x=v,
            y=h,
            w=self.w - v * 2,
            h=self.h - h * 2,
        )


class Elem:
    name = None
    attrs = {}
    units = {}

    def __init__(self, text=None, **attrs):
        self.text = text
        self.attrs = {
            **self.attrs,
            **{k.replace('_', '-'): v for k, v in attrs.items()},
        }

    def __str__(self):
        attrs = []
        for k, v in self.attrs.items():
            v = str(v) + self.units.get(k, '')
            attrs.append(f'{k}="{v}"')
        attrs = (' ' if attrs else '') + ' '.join(attrs)
        if self.text is None:
            return f'<{self.name}{attrs} />'
        else:
            return f'<{self.name}{attrs}>{self.text}</{self.name}>'


class Rect(Elem):
    name = 'rect'
    units = {
        'x': 'mm',
        'y': 'mm',
        'width': 'mm',
        'height': 'mm',
    }
    attrs = {
        'stroke': 'black',
        'stroke-width': '0.3',
        'fill': 'white',
    }


class Line(Elem):
    name = 'line'
    units = {
        'x1': 'mm',
        'y1': 'mm',
        'x2': 'mm',
        'y2': 'mm',
    }
    attrs = {
        'stroke': 'black',
        'stroke-width': '0.3',
    }


class Text(Elem):
    name = 'text'
    units = {
        'x': 'mm',
        'y': 'mm',
        'font-size': 'mm',
        'fill': 'black',
    }
    attrs = {
        'font-size': 3,
        # 'font-family': 'Noto Sans Display',
        'font-family': 'Open Sans Condensed'
        # 'font-family': 'Ubuntu Condensed'
    }


class TopCal(Text):
    attrs = {
        'font-size': 3,
        # 'font-family': 'Noto Sans Display',
        'font-family': 'Open Sans Condensed'
        # 'font-family': 'Ubuntu Condensed'
    }


def itermonths(eventsfile: pathlib.Path, b: Box, start: datetime.date):
    cal = calendar.Calendar()
    date = start - datetime.timedelta(days=start.weekday())
    date = datetime.date(date.year, date.month, 1)

    h = 4
    w = b.w / 7 / 8
    w = (b.w + w) / 7 / 8
    l = b.l  # noqa
    t = b.t + h

    # Detect how many months we can fit
    months = []
    for i in range(7):
        month = cal.monthdatescalendar(date.year, date.month)
        months.append((date, month))
        _, days = calendar.monthrange(date.year, date.month)
        date += datetime.timedelta(days=days)

    # Yield years
    year = None
    for i, (date, month) in enumerate(months):
        if year is not None and year == date.year:
            continue
        year = date.year
        yield TopCal(
            year,
            x=l + 8 * w * i,
            y=t,
        )
    t += h

    # Yield month names
    names = [
        'Sausis',
        'Vasaris',
        'Kovas',
        'Balandis',
        'Gegu????',
        'Bir??elis',
        'Liepa',
        'Rugpj??tis',
        'Rugs??jis',
        'Spalis',
        'Lapkritis',
        'Gruodis',
    ]
    for i, (date, month) in enumerate(months):
        name = [
            names[date.month - 1],
            calendar.month_name[date.month],
            str(date.month),
        ]
        yield TopCal(
            ' | '.join(name),
            x=l + 8 * i * w,
            y=t,
        )
    t += h

    # Yield week names
    for i, (date, month) in enumerate(months):
        for week in range(7):
            yield TopCal(
                calendar.day_abbr[week][:2],
                x=l + w + 8 * i * w + week * w,
                y=t,
                text_anchor='end',
            )
    t += h

    # Highligh current weeks
    end = start + datetime.timedelta(days=7 * 4)
    for i, (date, month) in enumerate(months):
        if month[0][-1] > end:
            continue
        top = None
        bot = None
        for j, week in enumerate(month):
            if top is None and week[-1] >= start:
                top = j
            if top is not None and bot is None and week[-1] >= end:
                bot = j
                break
        if top is None and bot is None:
            continue
        if top is None:
            top = 0
        if bot is None:
            bot = len(month)
        yield Rect(
            x=l + 8 * i * w,
            y=t + top * h - h + 1,
            width=w * 7 + 2,
            height=(bot - top) * h,
        )

    # Yield month days
    for i, (date, month) in enumerate(months):
        for j, week in enumerate(month):
            for k, d in enumerate(week):
                if d.month != date.month:
                    continue
                yield TopCal(
                    d.day,
                    x=l + w + 8 * i * w + k * w,
                    y=t + j * h,
                    text_anchor='end',
                )

    # Weekday names
    l -= .5  # noqa
    t += h * 6 + h
    w = b.w / 7
    h = (b.y + b.h - t) / 4
    names = [
        'Pirmadienis',
        'Antradienis',
        'Tre??iadienis',
        'Ketvirtadienis',
        'Penktadienis',
        '??e??tadienis',
        'Sekmadienis',
    ]
    for i in range(7):
        name = [
            names[i],
            calendar.day_name[i],
        ]
        yield Text(
            ' | '.join(name),
            x=l + i * w + 1,
            y=t - 1,
            font_size=4,
        )

    # Get events
    end = start + datetime.timedelta(days=7 * 4 + 7)
    events = get_events(
        eventsfile,
        datetime.datetime.combine(start, datetime.datetime.min.time()),
        datetime.datetime.combine(end, datetime.datetime.min.time()),
    )

    # Yield highlighted days
    city = astral.LocationInfo("Vilnius")
    for i in range(4):
        for j in range(7):
            date = start + datetime.timedelta(days=i * 7 + j)
            yield Rect(
                x=l + j * w + 1,
                y=t + i * h + 1,
                width=w - 1,
                height=h - 1,
            )
            yield Text(
                date.day,
                x=l + j * w + 1 + 9,
                y=t + i * h + 1 + 8,
                font_size=10,
                text_anchor='end',
            )

            sun = astral.sun.sun(city.observer, date=date)

            # Sunrise
            sunrise = sun['sunrise']
            yield Text(
                f'???{sunrise.hour:02d}:{sunrise.minute:02d}',
                x=l + j * w + 1 + 1 + 9,
                y=t + i * h + 1 + 3.5,
                font_size=3.5,
            )

            # Sunset
            sunset = sun['sunset']
            yield Text(
                f'???{sunset.hour:02d}:{sunset.minute:02d}',
                x=l + j * w + 1 + 1 + 9,
                y=t + i * h + 1 + 8,
                font_size=3.5,
            )

            # Daylight
            daylight = sunset - sunrise
            hours, remainder = divmod(daylight.seconds, 3600)
            minutes = remainder // 60
            yield Text(
                f'??? {hours:02d}:{minutes:02d}',
                x=l + j * w + 1 + 1 + 21,
                y=t + i * h + 1 + 3.5,
                font_size=3.5,
            )

            # Night
            sun = astral.sun.sun(city.observer, date=date + datetime.timedelta(days=1))
            sunrise = sun['sunrise']
            night = sunrise - sunset
            hours, remainder = divmod(night.seconds, 3600)
            minutes = remainder // 60
            phases = [
                '????',
                '????',
                '????',
                '????',
                '????',
                '????',
                '????',
                '????',
            ]
            phase = day_to_moon_phase_code(date)
            phase = phases[phase]
            yield Text(
                f'{phase} {hours:02d}:{minutes:02d}',
                x=l + j * w + 1 + 1 + 20,
                y=t + i * h + 1 + 8,
                font_size=3.5,
            )

            # Zodiac signs
            zodiac = {
                3: ('???', 'Avinas', 'Aries', 21),
                4: ('???', 'Jautis', 'Taurus', 21),
                5: ('????', 'Dvyniai', 'Gemini', 23),
                6: ('????', 'V????ys', 'Cancer', 22),
                7: ('????', 'Li??tas', 'Leo', 23),
                8: ('????', 'Mergel??', 'Virgo', 23),
                9: ('???', 'Svarstykl??s', 'Libra', 23),
                10: ('????', 'Skorpionas', 'Scorpius', 23),
                11: ('???', '??aulys', 'Sagittarius', 23),
                12: ('???', 'O??iaragis', 'Capricorn', 22),
                1: ('???', 'Vandenis', 'Aquarius', 21),
                2: ('???', '??uvys', 'Pisces', 20),
            }
            zodiac[0] = [12]
            if zodiac[date.month][-1] > date.day:
                sign = zodiac[date.month - 1][0]
            else:
                sign = zodiac[date.month][0]
            yield Text(
                sign,
                x=l + j * w + 1 + 1 + 33,
                y=t + i * h + 1 + 3.5,
                font_size=3.5,
            )

            # Show events
            for k, event in enumerate(events[date]):
                if len(event) > 1 and event[1] == ' ':
                    icon, text = event.split(None, 1)
                else:
                    icon = None
                    text = event

                if icon:
                    yield Text(
                        icon,
                        x=l + j * w + 1 + 3,
                        y=t + i * h + 1 + 13 + k * 4,
                        font_size=3.5,
                        text_anchor='middle',
                    )

                yield Text(
                    text,
                    x=l + j * w + 1 + 1 + 5,
                    y=t + i * h + 1 + 13 + k * 4,
                    font_size=3.5,
                )


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


def write_svg(eventsfile: pathlib.Path, date: datetime.date, output: pathlib.Path):
    # A4 paper
    p = Box(w=297, h=210)

    # Main canvas
    c = Box(
        p,
        x=10,
        y=20,
        w=p.w - 10 * 2,
        h=p.h - 30,
    )

    # Line markers at the top of page
    markers = ''.join(
        str(Line(x1=x, y1=0, x2=x, y2=20))
        for x in [
            p.w / 2,
            p.w / 2 - 40,
            p.w / 2 + 40,
        ]
    )

    months = ''.join(str(el) for el in itermonths(eventsfile, c, date))

    svg = f"""
    <svg version="1.1"
        baseProfile="full"
        width="{p.w}mm" height="{p.h}mm"
        xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="white" />
        {markers}
        {months}
    </svg>
    """

    outfile = output / f'{date}.svg'
    print(outfile)
    with outfile.open('w') as f:
        f.write(svg)


def get_events(eventsfile: pathlib.Path, start: datetime.datetime, end: datetime.datetime):
    events = collections.defaultdict(list)
    with eventsfile.open() as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if line == '' or line.startswith('#'):
                continue
            title, etype, line = map(str.strip, line.split(';', 2))
            assert etype in ('bday', 'powersof10', 'event'), f"Unknown event type {etype!r} in line {i}."

            if etype == 'bday':
                dtstart, rrule = map(str.strip, line.split(';', 1))
                dtstart = datetime.datetime.strptime(dtstart, '%Y-%m-%d')
                rule = dateutil.rrule.rrulestr(rrule, dtstart=dtstart)
                for d in rule.between(start, end, inc=True):
                    age = d.year - dtstart.year
                    events[d.date()].append(title.format(age=age))
            elif etype == 'powersof10':
                dtstart = line.strip()
                dtstart = datetime.datetime.strptime(dtstart, '%Y-%m-%d')
                units = (
                    ('MONTHLY', 'm??n.', range(2, 4)),
                    ('WEEKLY', 'sav.', range(2, 4)),
                    ('DAILY', 'd.', range(2, 5)),
                    ('HOURLY', 'val.', range(4, 6)),
                    ('MINUTELY', 'min.', range(6, 8)),
                    ('SECONDLY', 'sek.', range(8, 10)),
                )
                for freq, unit, powers in units:
                    for power in powers:
                        interval = 10**power
                        rrule = f'RRULE:FREQ={freq};INTERVAL={interval};COUNT=2'
                        rule = dateutil.rrule.rrulestr(rrule, dtstart=dtstart)
                        for d in rule.between(
                            max(dtstart + datetime.timedelta(days=1), start),
                            end,
                            inc=True,
                        ):
                            if power > 3:
                                age = f'10^{power} {unit}'
                            else:
                                age = f'{interval} {unit}'
                            events[d.date()].append(title.format(age=age))
            else:
                rrule = line.strip()
                rule = dateutil.rrule.rrulestr(rrule, dtstart=start)
                for d in rule.between(start, end, inc=True):
                    events[d.date()].append(title)

    return events


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('events', type=pathlib.Path)
    parser.add_argument('date', default=datetime.date.today().isoformat())
    parser.add_argument('-n', type=int, default=1)
    args = parser.parse_args()

    date = dateutil.parser.parse(args.date).date()

    output = pathlib.Path('output')
    output.mkdir(exist_ok=True)
    for p in output.glob('*.svg'):
        p.unlink()

    for i in range(args.n):
        write_svg(args.events, date, output)
        date += datetime.timedelta(days=7 * 4)
