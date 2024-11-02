import argparse

from xonsh.built_ins import XSH

import unreasonably_long_core as _uhucore
from unreasonably_long_core import uhu_aliases
from unreasonably_long_core.util import ScriptExit

parser = argparse.ArgumentParser()
parser.add_argument(
    "shortcut",
    help="Manually specify a shortcut name",
    type=str,
    default=None,
    nargs="?",
)
parser.add_argument(
    "-c",
    "--clear",
    help="Clear all stored shortcuts, or a specific command if you specify the name",
    action="store_true",
    default=False,
)
parser.add_argument(
    "-l", "--list", help="List all stored shortcuts", action="store_true", default=False
)


def _uhu(args: list[str]):
    parsed_args = parser.parse_args(args)

    try:
        if parsed_args.list:
            print("Not implemented yet")
        elif parsed_args.clear:
            if parsed_args.shortcut:
                _uhucore.delete_shortcut(parsed_args.shortcut)
            else:
                _uhucore.clear()
        else:
            _uhucore.alias_last_command(parsed_args.shortcut)
    except ScriptExit:
        pass


for alias in uhu_aliases:
    XSH.aliases[alias] = _uhu
