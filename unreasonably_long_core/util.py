from xonsh.built_ins import XSH


class ScriptExit(Exception):
    pass


_env = XSH.env


def script_exit() -> None:
    raise ScriptExit()


def _env_int_or_default(varname: str, default: int) -> int:
    if varname in _env:
        try:
            return int(env[varname])
        except ValueError:
            print(f"[red]💢 [bold]${varname}[/bold] should be an INTEGER")
            raise ScriptExit()
    else:
        return default


def _env_float_or_default(varname: str, default: float) -> float:
    if varname in _env:
        try:
            return float(_env[varname])
        except ValueError:
            print(f"[red]💢 [bold]${varname}[/bold] should be a NUMBER")
            raise ScriptExit()
    else:
        return default
