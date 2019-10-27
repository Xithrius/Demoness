"""
>> Demoness
> Copyright (c) 2019 Xithrius
> MIT license, Refer to LICENSE for more info
"""


import sys
import datetime
import os


def path(*filepath):
    """Gives a path relative to caller file location with added items.

    Args:
        objects: An amount of different items to path to as strings.

    Returns:
        A Path joined by the operating system's seperator.

    """
    return f'{os.path.abspath(os.path.dirname(sys.argv[0]))}{os.sep}{(os.sep).join(str(y) for y in filepath)}'


class cs:
    """A string including another thing, automated."""

    @classmethod
    def insert_items(cls, warning, string):
        """

        Args:
            warning: string of what the warning should say
            string: description of the warning

        Returns:
            A string with a date, warning, and string.

        """
        rn = now()
        s = [
            f"[{rn.strftime('%A %I:%M:%S')}{rn.strftime('%p').lower()}]",
            f'[ {warning} ]:',
            f'{string} '
        ]
        return ' '.join(str(y) for y in s)

    @classmethod
    def insert_block(cls, language, warning, string):
        return f'```{language}\n{warning} {string}\n```'

    @classmethod
    def w(cls, *string):
        """Returns a warning string."""
        print(cls.insert_items('Warning', ' '.join(string)))

    @classmethod
    def f(cls, *string):
        """Returns a fatal string."""
        print(cls.insert_items('Fatal', ' '.join(string)))

    @classmethod
    def s(cls, *string):
        """Returns a success string."""
        print(cls.insert_items('Success', ' '.join(string)))

    @classmethod
    def r(cls, *string):
        """Returns a custom warning string."""
        print(cls.insert_items('Ready', ' '.join(string)))

    @classmethod
    def css(cls, string):
        """Returns a block quote containing css colour-coded words."""
        return cls.insert_block('css', '--!>', string)


def now():
    """Returns the time depending on time zone from file

    Returns:
        The current date down to the millisecond.

    """
    return datetime.datetime.now()
