import ast
import builtins
import json
import sys
from shutil import which

import httpx
from rich import print
from rich.console import Console
from xonsh.built_ins import XSH
from xonsh.execer import Execer
from xonsh.history.base import HistoryEntry
from xonsh.procs.pipelines import HiddenCommandPipeline
from xonsh.shell import transform_command
from xonsh.shells.base_shell import BaseShell
from xonsh.tools import XonshError, print_exception, uncapturable, unthreadable

from uhu_core.util import (
    ScriptExit,
    env_float_or_default,
    env_int_or_default,
    script_exit,
)

uhu_aliases = ["huh", "uhu"]

_env = XSH.env
_console = Console()
_default_system_prompt = "You will generate a `shortname` for the provided xonsh command, which will be used as a convenient shortcut for it. Make the name memorable, but short. Do NOT use the command name for the `shortname`. Avoid using underscores, dashes and mixed case. Avoid making the alias an acronym. You may consider the `directory`, which is where the command was executed. Respond in JSON."
_stored_shortcuts: set[str] = set()
_last_created_alias: str | None = None


def clear() -> None:
    for shortcut in _stored_shortcuts:
        del XSH.aliases[shortcut]
        print(f"🗑️ Removed shortcut '{shortcut}'")

    _stored_shortcuts.clear()


def delete_shortcut(shortcut: str, *, message: bool = True) -> None:
    del XSH.aliases[shortcut]
    _stored_shortcuts.remove(shortcut)

    if message:
        print(f"🗑️ Removed shortcut '{shortcut}'")


def alias_last_command(name: str | None) -> None:
    last_command, is_renaming = _get_last_command()

    if name is None:
        name = _generate_alias(last_command, is_renaming)
    elif not _is_new_alias_ok(name):
        print(f"💢 Bad human! Tried to shadow '{name}'")
        script_exit()

    _create_alias(name, last_command, is_renaming)


def _create_alias(name: str, command: HistoryEntry, is_renaming: bool) -> None:
    global _last_created_alias

    @unthreadable
    @uncapturable
    def _alias(args: list[str]) -> any:
        nonlocal command
        res = _exec_alias(command, args)

        # Subprocess commands already printed to console
        if not isinstance(res, HiddenCommandPipeline):
            return res

    XSH.aliases[name] = _alias
    _stored_shortcuts.add(name)

    if not is_renaming:
        print(f"✨ Last command shortened to '{name}'")
    else:
        print(f"✨ Renamed '{_last_created_alias}' to '{name}'")
        delete_shortcut(_last_created_alias, message=False)

    _last_created_alias = name


def _exec_alias(command: HistoryEntry, args: list[str]) -> any:
    # We want to execute the command with arguments and with the current context
    # (and not an isolated one without the variables/aliases defined in this one),
    # and also not affect the history, so we need to use shell internals.
    # See `base_shell.BaseShell.default` for reference.
    # This is a GLORIOUS STATE APPROVED HACK!!!

    line = _build_line(command, args)
    shell: BaseShell = XSH.shell.shell
    execer: Execer = shell.execer

    try:

        def try_exec(line):
            nonlocal shell
            # todo do I need to transform the line?
            tree = execer.parse(line, set(dir(builtins)) | set(shell.ctx.keys()))

            modes = {ast.Module: "exec", ast.Expression: "eval"}
            code = compile(tree, "<uhu>", modes[type(tree)])

            return eval(code, shell.ctx)

        # Honestly, I have no idea how xonsh does this, so here is my shitty bootleg
        try:
            return try_exec(line)
        except SyntaxError as e:
            if e.msg == "None: no further code":
                return try_exec(line + "\n")
            else:
                raise e

    except XonshError as e:
        print(e.args[0], file=sys.stderr)
    except (SystemExit, KeyboardInterrupt) as err:
        raise err
    except BaseException:
        type_, value, traceback = sys.exc_info()
        # strip off the current frame as the traceback should only show user code
        traceback = traceback.tb_next

        print_exception(exc_info=(type_, value, traceback))
    finally:
        # thank god this isn't java
        # noinspection PyProtectedMember
        shell._fix_cwd()


def _build_line(command: HistoryEntry, args: list[str]) -> str:
    line = command.cmd.strip()
    if args:
        line += " " + " ".join(args).strip()
    line = transform_command(line + "\n").strip()
    return line


def _get_last_command() -> tuple[HistoryEntry, bool]:
    is_renaming = False
    index = -1

    while True:
        try:
            last = XSH.history[index]

            if any(filter(last.cmd.startswith, uhu_aliases)):
                index -= 1
                is_renaming = True
            else:
                break
        except IndexError:
            print("[red]💢 There's no history! What the hell do you want me to do?!")
            script_exit()

    return last, is_renaming


def _generate_alias(command: HistoryEntry, is_renaming: bool) -> str:
    blacklist = []

    if is_renaming:
        blacklist.append(_last_created_alias)

    max_tries = max(env_int_or_default("XONSH_UHU_MAX_LLM_TRIES", 3), 1)

    for i in range(0, max_tries):
        alias = _prompt_ai_for_alias(command=command, blacklist=blacklist)

        if not _is_new_alias_ok(alias):
            print(f"💢 Bad LLM! Tried to shadow '{alias}'")
            blacklist.append(alias)
        else:
            return alias

    print(
        f"[red]{'💢' * max_tries} LLM would not generate a valid name after {max_tries} tries."
    )
    script_exit()


def _is_new_alias_ok(alias: str) -> bool:
    return not (
        alias in XSH.aliases or alias in uhu_aliases or which(alias) is not None
    )


def _prompt_ai_for_alias(*, command: HistoryEntry, blacklist: list[str]) -> str:
    if _env.get("XONSH_UHU_MODEL_NAME", None) is None:
        print("[red]💢 You haven't set [bold]$XONSH_UHU_MODEL_NAME[/bold] !")
        script_exit()

    prompt = dict(directory=command.cwd, command=command.cmd.strip())

    if blacklist:
        prompt["names_blacklist"] = blacklist

    model = _env.get("XONSH_UHU_MODEL_NAME")
    system_prompt = _env.get("XONSH_UHU_SYSTEM_PROMPT", _default_system_prompt)

    result = _call_ai(
        model=model,
        system=system_prompt,
        temperature=0.2,
        prompt=json.dumps(prompt),
    )

    return result["shortname"].strip().lower()


def _call_ai(
    model: str, prompt: str, system: str, temperature: float
) -> dict[str, str]:
    ollama_url = httpx.URL(_env.get("XONSH_UHU_OLLAMA_URL", "http://localhost:11434"))

    try:
        with _console.status("Waiting for ollama"):
            api_result = httpx.post(
                ollama_url.join("api/generate"),
                json={
                    "model": model,
                    "format": "json",
                    "stream": False,
                    "prompt": prompt,
                    "system": system,
                    "options": {"temperature": temperature},
                },
                timeout=env_float_or_default("XONSH_UHU_OLLAMA_TIMEOUT", 30.0),
            )
    except httpx.UnsupportedProtocol as e:
        print(f"[red]💢 {str(e).rstrip('.')}!")
        raise ScriptExit()
    except httpx.ConnectError:
        print(f"[red]💢 Couldn't connect to {ollama_url}!")
        raise ScriptExit()
    except httpx.TimeoutException:
        print(
            f"[red]💢 Your computer is too slow!! Could it be that you don't own a [bold]BakaTX 8090 Tie[/bold]?!? Y-You DO know the more you buy, the more you save, r-right??\n"
            "💢 ...I-It's not like you could increase [bold]$XONSH_UHU_OLLAMA_TIMEOUT[/bold] or anything!! B-Baka!!!"
        )
        raise ScriptExit()
    else:
        if not api_result.is_success:
            print("[red]💢 Ollama error!")
            print(f"HTTP {api_result.status_code}:")
            print(api_result.text)
            script_exit()

        api_data = json.loads(api_result.text)
        return json.loads(api_data["response"])
