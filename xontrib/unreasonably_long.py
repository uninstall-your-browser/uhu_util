import argparse
from ast import parse

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
#todo just re-use `shortcut`, this doesn't need to have any value
parser.add_argument(
    "-c",
    "--clear",
    help="Clear all stored shortcuts, or a specific command if you specify the name",
    nargs="?",
    type=str,
    const=True,
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
        elif parsed_args.clear is True:
            _uhucore.clear()
        elif isinstance(parsed_args.clear, str):
            _uhucore.delete_shortcut(parsed_args.clear)
        else:
            _uhucore.alias_last_command(parsed_args.shortcut)
    except ScriptExit:
        pass


for alias in uhu_aliases:
    XSH.aliases[alias] = _uhu
