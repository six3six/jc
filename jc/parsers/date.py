"""jc - JSON CLI output utility `date` command output parser

The `epoch` calculated timestamp field is naive. (i.e. based on the local time of the system the parser is run on)

The `epoch_utc` calculated timestamp field is timezone-aware and is only available if the timezone field is UTC.

Usage (cli):

    $ date | jc --date

    or

    $ jc date

Usage (module):

    import jc.parsers.date
    result = jc.parsers.date.parse(date_command_output)

Compatibility:

    'linux', 'darwin', 'freebsd'

Examples:

    $ date | jc --date -p
    {
      "year": 2021,
      "month_num": 3,
      "day": 23,
      "hour": 8,
      "hour_24": 20,
      "minute": 45,
      "second": 29,
      "period": "PM",
      "month": "Mar",
      "weekday": "Tue",
      "weekday_num": 2,
      "timezone": "UTC",
      "epoch": 1616557529,
      "epoch_utc": 1616532329
    }

    $ date | jc --date -p -r
    {
      "year": "2021",
      "month": "Mar",
      "day": "23",
      "weekday": "Tue",
      "hour": "08",
      "minute": "45",
      "second": "29",
      "period": "PM",
      "timezone": "UTC"
    }
"""
from datetime import datetime, timezone
import jc.utils


class info():
    version = '1.2'
    description = 'date command parser'
    author = 'Kelly Brazil'
    author_email = 'kellyjonbrazil@gmail.com'

    # compatible options: linux, darwin, cygwin, win32, aix, freebsd
    compatible = ['linux', 'darwin', 'freebsd']
    magic_commands = ['date']


__version__ = info.version


def process(proc_data):
    """
    Final processing to conform to the schema.

    Parameters:

        proc_data:   (Dictionary) raw structured data to process

    Returns:

        Dictionary. Structured data with the following schema:

        {
          "year":         integer,
          "month_num":    integer,
          "day":          integer,
          "hour":         integer,       # originally parsed hour
          "hour_24":      integer,       # parsed hour converted to 24-hour value
          "minute":       integer,
          "second":       integer,
          "period":       string,        # 'AM' or 'PM'. null if 24-hour output
          "month":        string,
          "weekday":      string,
          "weekday_num":  integer,
          "timezone":     string,
          "epoch":        integer,       # naive timestamp
          "epoch_utc":    integer,       # timezone-aware timestamp. Only available if timezone field is UTC
        }
    """
    # ISO 8601 month numberings
    month_map = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12
    }

    # ISO 8601 weekday numberings
    weekday_map = {
        "Mon": 1,
        "Tue": 2,
        "Wed": 3,
        "Thu": 4,
        "Fri": 5,
        "Sat": 6,
        "Sun": 7
    }

    if proc_data:
        dt_year = int(proc_data['year'])
        dt_month = month_map[proc_data['month']]
        dt_day = int(proc_data['day'])
        dt_hour = int(proc_data['hour'])
        dt_hour_24 = int(proc_data['hour'])
        dt_minute = int(proc_data['minute'])
        dt_second = int(proc_data['second'])

        # fix for 12 vs. 24 hour output
        if 'period' in proc_data:
            if proc_data['period']:
                if proc_data['period'].lower() == 'pm':
                    dt_hour_24 = dt_hour + 12
                    if dt_hour_24 > 23:
                        dt_hour_24 = 12
                if proc_data['period'].lower() == 'am':
                    if dt_hour_24 == 12:
                        dt_hour_24 = 0

        epoch_dt = datetime(dt_year, dt_month, dt_day, hour=dt_hour_24, minute=dt_minute, second=dt_second)

        date_obj = {
            'year': dt_year,
            'month_num': dt_month,
            'day': dt_day,
            'hour': dt_hour,
            'hour_24': dt_hour_24,
            'minute': dt_minute,
            'second': dt_second,
            'period': proc_data['period'].upper() if 'period' in proc_data else None,
            'month': proc_data['month'],
            'weekday': proc_data['weekday'],
            'weekday_num': weekday_map[proc_data['weekday']],
            'timezone': proc_data['timezone'],
            'epoch': int(epoch_dt.timestamp())
        }

        # create aware datetime object only if the timezone is UTC
        if proc_data['timezone'] == 'UTC':
            utc_epoch_dt = datetime(dt_year, dt_month, dt_day, hour=dt_hour_24, minute=dt_minute, second=dt_second, tzinfo=timezone.utc)
            date_obj['epoch_utc'] = int(utc_epoch_dt.timestamp())

        return date_obj

    else:
        return {}


def parse(data, raw=False, quiet=False):
    """
    Main text parsing function

    Parameters:

        data:        (string)  text data to parse
        raw:         (boolean) output preprocessed JSON if True
        quiet:       (boolean) suppress warning messages if True

    Returns:

        Dictionary. Raw or processed structured data.
    """
    if not quiet:
        jc.utils.compatibility(__name__, info.compatible)

    raw_output = {}

    if jc.utils.has_data(data):
        data = data.replace(':', ' ')
        split_data = data.split()

        # date v8.32 uses a different format depending on locale, so need to support LANG=en_US.UTF-8
        if len(split_data) == 9 and ('AM' in split_data or 'am' in split_data or 'PM' in split_data or 'pm' in split_data):
            raw_output = {
                "year": split_data[8],
                "month": split_data[1],
                "day": split_data[2],
                "weekday": split_data[0],
                "hour": split_data[3],
                "minute": split_data[4],
                "second": split_data[5],
                "period": split_data[6],
                "timezone": split_data[7]
            }
        else:
            # standard LANG=C date output
            raw_output = {
                "year": split_data[7],
                "month": split_data[1],
                "day": split_data[2],
                "weekday": split_data[0],
                "hour": split_data[3],
                "minute": split_data[4],
                "second": split_data[5],
                "timezone": split_data[6]
            }

    if raw:
        return raw_output
    else:
        return process(raw_output)
