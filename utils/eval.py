import logging
import textwrap

from contextlib import redirect_stdout
from io import StringIO
from traceback import format_exc

log = logging.getLogger(__name__)


async def evaluate(bot, body):
    env = {"bot": bot}
    env.update(globals())
    stdout = StringIO()
    to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'
    try:
        exec(to_compile, env)
    except Exception as e:
        return f"```py\n{e.__class__.__name__}: {e}\n```"

    func = env["func"]
    try:
        with redirect_stdout(stdout):
            ret = await func()
    except Exception:
        value = stdout.getvalue()
        return f"```py\n{value}{format_exc()}\n```"
    else:
        value = stdout.getvalue()

        if ret is None:
            if value:
                return f"```py\n{value}\n```"
        else:
            return f"```py\n{value}{ret}\n```"
