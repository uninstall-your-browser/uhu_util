class ScriptExit(Exception):
    pass


def script_exit() -> None:
    raise ScriptExit()
