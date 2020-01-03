import calendar
import datetime


class Box:

    def __init__(
        self,
        w: int = 1,
        h: int = 1,
        x: int = 0,
        y: int = 0,
    ):
        self.w = w
        self.h = h
        self.x = x
        self.y = y


def itermonths(canvas: Box, start: datetime.date):
    cal = calendar.Calendar()
    dates = cal.itermonthdates(start.year, start.month)
    date = next(dates)
    date = datetime.date(date.year, date.month, 1)

    h = 3
    w = 5
    t = canvas.y + h

    # Detect how many months we can fit
    maxw = 0
    months = []
    while True:
        month = cal.monthdatescalendar(date.year, date.month)
        maxw += len(month) * w
        if maxw > canvas.w:
            break
        months.append((date, month))
        _, days = calendar.monthrange(date.year, date.month)
        date += datetime.timedelta(days=days)

    # Yield years
    x = 0
    year = None
    for date, month in months:
        if year is not None and year == date.year:
            continue
        year = date.year
        b = Box(
            x=canvas.x + w + w * x,
            y=t,
            h=h, w=w,
        )
        yield b, year, 'start'
        x += len(month)
    t += h

    # Yield month names
    x = 0
    for date, month in months:
        b = Box(
            x=canvas.x + w + w * x,
            y=t,
            h=h, w=w,
        )
        yield b, MONTHNAMES[date.month], 'start'
        x += len(month)
    t += h

    # Yield week names
    for y, name in enumerate(('P', 'A', 'T', 'K', 'P', 'Š', 'S')):
        b = Box(
            x=canvas.x,
            y=t + h * y,
            h=h, w=w,
        )
        yield b, name, 'start'

    # Yield mont days
    x = 0
    for date, month in months:
        for week in month:
            for i, d in enumerate(week):
                if d.month != date.month:
                    continue
                y = d.weekday()
                b = Box(
                    x=canvas.x + w + w * x,
                    y=t + h * y,
                    h=h, w=w,
                )
                yield b, d.day, 'end'
            x += 1


MONTHNAMES = {
    1: 'Sausis',
    2: 'Vasaris',
    3: 'Kovas',
    4: 'Balandis',
    5: 'Gegužė',
    6: 'Birželis',
    7: 'Liepa',
    8: 'Rugpjūtis',
    9: 'Rugsėjis',
    10: 'Spalis',
    11: 'Lapkritis',
    12: 'Gruodis',
}


# A4 paper
p = Box(w=297, h=210)

# Main canvas
c = Box(
    x=10, w=p.w - 20,
    y=10, h=p.h - 20,
)

# Start date
start = datetime.date(2020, 1, 3)

months = list(itermonths(c, start))

months = ''.join(
    f'<text x="{b.x}mm" y="{b.y}mm" font-size="{b.h}mm" text-anchor="{anchor}" fill="black">{v}</text>'
    for b, v, anchor in months
)

svg = f"""
<svg version="1.1"
     baseProfile="full"
     width="{p.w}mm" height="{p.h}mm"
     xmlns="http://www.w3.org/2000/svg">

  <rect width="100%" height="100%" fill="white" />
  <rect x="{c.x}mm" y="{c.y}mm"  width="{c.w}mm" height="{c.h}mm" fill="transparent"  stroke="black" stroke-width="1" />

  {months}

</svg>
"""

with open('out.svg', 'w') as f:
    f.write(svg)
