import discord
import io
import os
import json
import textwrap
import traceback
from contextlib import redirect_stdout
from discord.ext import commands


# Borrowed from https://github.com/chenzw95/porygon/blob/master/cogs/debug.py with slight modifications
class PythonInterpreter(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        with open('saves/banned_phrases.json', 'r') as f:
            self.banned_phrases = json.load(f)
        print(f'Addon "{self.__class__.__name__}" loaded')

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
        to_compile = f"async def func():\n{textwrap.indent(body, '  ')}"
        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```\n{e.__class__.__name__}: {e}\n```')
        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.message.add_reaction("❌")
            await ctx.send(f'```\n{value}{traceback.format_exc()}\n```')
        else:
            await ctx.message.add_reaction("✅")
            value = stdout.getvalue()
            result = None
            if ret is None:
                if value:
                    result = f'```\n{value}\n```'
                else:
                    try:
                        result = f'```\n{repr(eval(body, env))}\n```'
                    except:
                        pass
            else:
                self._last_result = ret
                result = f'```\n{value}{ret}\n```'
            if result:
                log_msg = body.replace('`', r'\`')
                if not log_msg[0:3] == '```':
                    log_msg = '```' + log_msg + '```'
                await self.bot.interpreter_logs_channel.send(f"Interpreter used by {ctx.author} in {ctx.channel.mention}:\n{log_msg}")
                if len(str(result)) > 1900:
                    await ctx.send("Large output:", file=discord.File(io.BytesIO(result.encode("utf-8")), filename="output.txt"))
                    await self.bot.interpreter_logs_channel.send("Large Result:", file=discord.File(io.BytesIO(result.encode("utf-8")), filename="output.txt"))
                    for user in (self.bot.creator, self.bot.allen, self.bot.pie):
                        await user.send("Large Result:", file=discord.File(io.BytesIO(result.encode("utf-8")), filename="output.txt"))
                else:
                    await ctx.send(result)
                    await self.bot.interpreter_logs_channel.send(f"Result: {result}")
                    for user in (self.bot.creator, self.bot.allen, self.bot.pie):
                        await user.send(f"Result: {result}")


    @commands.group(hidden=True)
    @commands.has_any_role("Bot Dev", "FlagBrew Team", "Discord Moderator")
    async def py(self, ctx, *, msg):
        """Python interpreter. Limited to bot devs, flagbrew team, and staff"""
        if any(b in msg for b in self.banned_phrases):
            return await ctx.send("Something in your code isn't allowed. Cancelling code execution.")
        log_msg = self.cleanup_code(msg).replace('`', r'\`')
        if not log_msg[0:3] == '```':
            log_msg = '```' + log_msg + '```'
        for user in (self.bot.creator, self.bot.allen, self.bot.pie):
            await user.send(f"Interpreter used by {ctx.author} in {ctx.channel.mention}:\n{log_msg}")
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

    @commands.command()
    @commands.has_any_role("Discord Moderator", "Bot Dev")
    async def togglepy(self, ctx):
        """Toggles the python interpreter. Bot creator and allen only"""
        if not ctx.author in (self.bot.creator, self.bot.allen):
            raise commands.errors.CheckFailure()
        pycmd = self.bot.get_command('py')
        if pycmd.enabled:
            pycmd.enabled = False
            return await ctx.send("Disabled the py command!")
        else:
            pycmd.enabled = True
            return await ctx.send("Enabled the py command!")

    @commands.command(name='bp')
    @commands.has_any_role("Discord Moderator", "Bot Dev")
    async def banphrase(self, ctx, phrase):
        """Bans a phrase from the interpreter"""
        if not ctx.author in (self.bot.creator, self.bot.allen):
            raise commands.errors.CheckFailure()
        if phrase in self.banned_phrases:
            return await ctx.send(f"`{phrase}` is already banned!")
        self.banned_phrases.append(phrase)
        with open("saves/banned_phrases.json", "w") as f:
            json.dump(self.banned_phrases, f, indent=4)
        await ctx.send(f"Added `{phrase}` to the banned phrase list.")

    @commands.command(name='ubp')
    @commands.has_any_role("Discord Moderator", "Bot Dev")
    async def unbanphrase(self, ctx, phrase):
        """Unbans a phrase from the interpreter"""
        if not ctx.author in (self.bot.creator, self.bot.allen):
            raise commands.errors.CheckFailure()
        if not phrase in self.banned_phrases:
            return await ctx.send(f"`{phrase}` isn't a banned phrase!")
        self.banned_phrases.remove(phrase)
        with open("saves/banned_phrases.json", "w") as f:
            json.dump(self.banned_phrases, f, indent=4)
        await ctx.send(f"Removed `{phrase}` from the banned phrase list.")

    @commands.command(name='lbp')
    @commands.has_any_role("Bot Dev", "FlagBrew Team", "Discord Moderator")
    async def listbannedphrases(self, ctx):
        await ctx.send("Banned phrases:\n```{}\n{}```".format(self.banned_phrases[0], "\n".join(self.banned_phrases)))


def setup(bot):
    bot.add_cog(PythonInterpreter(bot))