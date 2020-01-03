import calendar
import datetime
import astral


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
        'stroke-width': '1',
        'fill': 'transparent',
    }


class Text(Elem):
    name = 'text'
    units = {
        'x': 'mm',
        'y': 'mm',
        'font-size': 'mm',
        'fill': 'black',
    }


class TopCal(Text):
    attrs = {
        'font-size': 3,
    }


def itermonths(b: Box, start: datetime.date):
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
    for i, (date, month) in enumerate(months):
        yield TopCal(
            calendar.month_name[date.month] + f' | {date.month:02d}',
            x=l + 8 * i * w,
            y=t,
        )
    t += h

    # Yield week names
    for i, (date, month) in enumerate(months):
        for week in range(7):
            yield TopCal(
                calendar.day_abbr[week][:2],
                x=l + 8 * i * w + week * w,
                y=t,
            )
    t += h

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

    # Yield highlighted days
    a = astral.Astral()
    city = a['Vilnius']
    l -= .5  # noqa
    t += h * 6 + h
    w = b.w / 7
    h = (b.y + b.h - t) / 4
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
                x=l + j * w + 1 + 11,
                y=t + i * h + 1 + 8,
                font_size=10,
                text_anchor='end',
            )

            sun = city.sun(date=date, local=True)

            # Sunrise
            sunrise = sun['sunrise']
            yield Text(
                f'↑{sunrise.hour:02d}:{sunrise.minute:02d}',
                x=l + j * w + 1 + 1 + 12,
                y=t + i * h + 1 + 3.5,
                font_size=3.5,
            )

            # Sunset
            sunset = sun['sunset']
            yield Text(
                f'↓{sunset.hour:02d}:{sunset.minute:02d}',
                x=l + j * w + 1 + 1 + 12,
                y=t + i * h + 1 + 8,
                font_size=3.5,
            )

            # Daylight
            daylight = sunset - sunrise
            hours, remainder = divmod(daylight.seconds, 3600)
            minutes = remainder // 60
            yield Text(
                f'☀{hours:02d}:{minutes:02d}',
                x=l + j * w + 1 + 1 + 24,
                y=t + i * h + 1 + 3.5,
                font_size=3.5,
            )

            # Night
            sun = city.sun(date=date + datetime.timedelta(days=1), local=True)
            sunrise = sun['sunrise']
            night = sunrise - sunset
            hours, remainder = divmod(night.seconds, 3600)
            minutes = remainder // 60
            phases = [
                '🌑',
                '🌒',
                '🌓',
                '🌔',
                '🌕',
                '🌖',
                '🌗',
                '🌘',
            ]
            moon = a.moon_phase(date=date)
            moon = round(moon / 27 * 7)
            moon = phases[moon]
            yield Text(
                f'{moon}{hours:02d}:{minutes:02d}',
                x=l + j * w + 1 + 1 + 24,
                y=t + i * h + 1 + 8,
                font_size=3.5,
            )


# A4 paper
p = Box(w=297, h=210)

# Main canvas
c = p.shrink(10)

# Start date
start = datetime.date(2019, 12, 30)
# start = datetime.date(2020, 1, 27)
# start = datetime.date(2020, 2, 24)

months = ''.join(str(el) for el in itermonths(c, start))

svg = f"""
<svg version="1.1"
     baseProfile="full"
     width="{p.w}mm" height="{p.h}mm"
     xmlns="http://www.w3.org/2000/svg">

  <rect width="100%" height="100%" fill="white" />

  {months}

</svg>
"""

with open('out.svg', 'w') as f:
    f.write(svg)
