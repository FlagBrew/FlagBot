import discord
import io
import os
import textwrap
from contextlib import redirect_stdout
import traceback
from discord.ext import commands


# Borrowed from https://github.com/chenzw95/porygon/blob/master/cogs/debug.py with slight modifications
class PythonInterpreter(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])
        # remove `foo`
        return content.strip('` \n')

    # Executes/evaluates code.Pretty much the same as Rapptz implementation for RoboDanny with slight variations.
    async def interpreter(self, env, code, ctx):
        body = self.cleanup_code(code)
        stdout = io.StringIO()
        to_compile = 'async def func():\n{}'.format(textwrap.indent(body, "  "))
        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send('```\n{}: {}\n```'.format(e.__class__.__name__, e))
        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.message.add_reaction("❌")
            await ctx.send('```\n{}{}\n```'.format(value, traceback.format_exc()))
        else:
            await ctx.message.add_reaction("✅")
            value = stdout.getvalue()
            result = None
            if ret is None:
                if value:
                    result = '```\n{}\n```'.format(value)
                else:
                    try:
                        result = '```\n{}\n```'.format(repr(eval(body, env)))
                    except:
                        pass
            else:
                self._last_result = ret
                result = '```\n{}{}\n```'.format(value, ret)
            if result:
                if len(str(result)) > 1950:
                    await ctx.send("Large output:", file=discord.File(io.BytesIO(result.encode("utf-8")), filename="output.txt"))
                else:
                    await ctx.send(result)

    @commands.group(hidden=True)
    @commands.has_any_role("Bot Dev", "FlagBrew Team", "Discord Moderator")
    async def py(self, ctx, *, msg):
        """Python interpreter. Limited to bot devs, flagbrew team, and staff"""
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'server': ctx.guild,
            'message': ctx.message,
            '_': self._last_result
        }
        env.update(globals())
        await self.interpreter(env, msg, ctx)


def setup(bot):
    bot.add_cog(PythonInterpreter(bot))