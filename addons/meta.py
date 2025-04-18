import discord
import inspect
import io
import json
import asyncio
import os
from discord.ext import commands

#  Revised addon loading for Meta taken from https://stackoverflow.com/a/24940613
addons = {
    "addons.events": "Events",
    "addons.info": "Info",
    "addons.mod": "Moderation",
    "addons.pkhex": "pkhex",
    "addons.pyint": "PythonInterpreter",
    "addons.utility": "Utility",
    "addons.warns": "Warning"
}
keys = {}
failed_loads = {}
for addon in addons.keys():
    try:
        keys[addons[addon]] = __import__(addon, fromlist=addons[addon])
    except Exception as exception:
        failed_loads[addons[addon]] = exception


class Meta(commands.Cog, command_attrs=dict(hidden=True)):

    def __init__(self, bot):
        self.bot = bot
        self.addons = {}
        for key, val in keys.items():
            members = inspect.getmembers(keys[key], inspect.isclass)
            for cl in members:
                if not cl[0] in addons.values():
                    continue
                self.addons[val.__name__] = cl
        print(f'Addon "{self.__class__.__name__}" loaded')

    @commands.command(hidden=True)
    async def failedloads(self, ctx):
        if len(failed_loads) == 0:
            return await ctx.send("No modules failed to load!")
        await ctx.send(f"Failed to load: `{'`, `'.join(f'{a}` - `{e}' for a, e in failed_loads.items())}`")

    @commands.command(hidden=True)
    async def source(self, ctx, function, cl=None):
        """Gets the source code of a function / command. Limited to bot creator."""
        if not ctx.author == self.bot.creator:
            raise commands.errors.CheckFailure()
        command = self.bot.get_command(function)
        if command is None:
            if cl and not cl.startswith("addons."):
                cl = "addons." + cl
            if not cl or cl not in self.addons.keys():
                return await ctx.send("That isn't a command. Please supply a valid class name for retrieving functions.")
            try:
                cl_obj = self.addons[cl][1]
                func = getattr(cl_obj, function)
            except AttributeError:
                return await ctx.send(f"I couldn't find a function named `{function}` in the `{cl}` class.")
            src = inspect.getsource(func)
        else:
            src = inspect.getsource(command.callback)
        if len(src) < 1900:
            src = src.replace('`', r'\`')
            await ctx.send(f"Source code for the `{function}` command{' in the `' + cl + '` class' if cl in self.addons else ''}: ```py\n{src}\n```")
        else:
            await ctx.send(f"Source code for the `{function}` command{' in the `' + cl + '` class' if cl in self.addons else ''} (Large source code):", file=discord.File(io.BytesIO(src.encode("utf-8")), filename="output.py"))

    @commands.group()
    @commands.has_any_role("Bot Dev", "Discord Moderator")
    async def botedit(self, ctx):
        """Main handler for bot editing commands"""
        if ctx.invoked_subcommand is None:
            return await ctx.send("Possible subcommands: `activity`, `nick`, and `icon`.")

    @botedit.command()
    async def activity(self, ctx, activity_type=None, *, new_activity=None):
        """Changes the bot's activity. Giving no type and status will clear the activity."""
        activity_types = {
            "watching": discord.ActivityType.watching,
            "listening": discord.ActivityType.listening,
            "playing": discord.ActivityType.playing
        }
        if activity_type is None and new_activity is None:
            await self.bot.change_presence(activity=None)
            return await ctx.send("Cleared my activity.")
        elif activity_type is not None and new_activity is None:
            raise commands.errors.MissingRequiredArgument(inspect.Parameter(name='new_activity', kind=inspect.Parameter.POSITIONAL_ONLY))
        if not activity_type.lower() in activity_types:
            return await ctx.send(f"`{activity_type}` is not a valid activity type. Valid activity types: `{'`, `'.join(x for x in activity_types)}`.")
        elif len(new_activity) > 30:
            return await ctx.send(f"Activities must be limited to less than 30 characters. Inputted value length: {len(new_activity)} characters.")
        real_type = activity_types[activity_type.lower()]
        activity = discord.Activity(name=new_activity, type=real_type)
        await self.bot.change_presence(activity=activity)
        self.bot.persistent_vars_dict["activity"]["name"] = new_activity
        self.bot.persistent_vars_dict["activity"]["type"] = activity_type.lower()
        with open("saves/persistent_vars.json", "w") as file:
            json.dump(self.bot.persistent_vars_dict, file, indent=4)
        await ctx.send(f"Successfully changed my activity to: `{activity_type.title()} {new_activity}`.")

    @botedit.command()
    async def nick(self, ctx, *, nick=None):
        """Changes the bot's nick. Giving no nick will clear the nickname."""
        if nick is None:
            await ctx.me.edit(nick=None)
            return await ctx.send("Cleared my nickname.")
        elif len(nick) < 2 or len(nick) > 32:
            return await ctx.send(f"Nicknames must be greater than or equal to 2 characters, but less than 33 characters. Inputted value length: {len(nick)} characters.")
        await ctx.me.edit(nick=nick)
        await ctx.send(f"Successfully changed my nickname to: `{nick}`")

    @botedit.command()
    async def icon(self, ctx):
        """Changes the bot's icon. Attach a JPG or PNG to change it to that. Giving no attachment will revert to the FlagBrew icon."""
        if bool(ctx.message.attachments):
            icon = await ctx.message.attachments[0].read()
        else:
            async with self.bot.session.get(url='https://avatars.githubusercontent.com/u/42673825?s=200&v=4') as resp:
                icon = await resp.read()
        await self.bot.user.edit(avatar=icon)
        await ctx.send(f"Successfully changed my icon. Due to Discord's cache, this may require a reload to view.")

    @commands.command(name="license")
    async def flagbot_license(self, ctx):
        embed = discord.Embed(title="FlagBot's License")
        embed.description = ("FlagBrew's discord server moderation + utility bot"
                             "\nCopyright (C) **2018-2021** | **GriffinG1**"
                             "\n\nThis program is free software: you can redistribute it and/or modify\n"
                             "it under the terms of the GNU Affero General Public License as published\n"
                             "by the Free Software Foundation, either version 3 of the License, or\n"
                             "(at your option) any later version.\n"
                             "This program is distributed in the hope that it will be useful,\n"
                             "but WITHOUT ANY WARRANTY; without even the implied warranty of\n"
                             "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.\n"
                             "See the GNU Affero General Public License for more details.\n"
                             "A copy of the GNU Affero General Public License is available "
                             "[in the program's repository](https://github.com/FlagBrew/FlagBot/blob/master/LICENSE)."
                             )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_any_role("Admin", "Bot Dev")
    async def surprise(self, ctx):
        """Happy April 1st! Pass in image attachment for server icon change"""
        if not os.path.exists('saves/layout.json'):
            data = {}
            for c in ctx.guild.channels:
                data[c.id] = c.name
            with open('saves/layout.json', 'w') as file:
                json.dump(data, file, indent=4)
        with open('saves/new_layout.json', 'r') as file:
            new = json.load(file)
        for ch in new.keys():
            channel = ctx.guild.get_channel(int(ch))  # currently does not support threads. unsure if I'll add support
            if channel.name == new[ch]:
                continue
            await channel.edit(name=new[ch])
            await asyncio.sleep(3)
        if bool(ctx.message.attachments):
            img_bytes = await ctx.message.attachments[0].read()
        await ctx.guild.edit(icon=img_bytes)
        await ctx.send("Updated the channel list.")

    @commands.command()
    @commands.has_any_role("Admin", "Bot Dev")
    async def revert(self, ctx):
        """April 1st is over"""
        with open('saves/layout.json', 'r') as file:
            old = json.load(file)
        for ch in old.keys():
            channel = ctx.guild.get_channel(int(ch))  # currently does not support threads. unsure if I'll add support
            if channel.name == old[ch]:
                continue
            await channel.edit(name=old[ch])
            await asyncio.sleep(3)
        async with self.bot.session.get(url='https://avatars.githubusercontent.com/u/42673825?s=200&v=4') as resp:
            r_data = await resp.read()
            await ctx.guild.edit(icon=r_data)
        await ctx.send("Reverted back the channel list.")

    @commands.command()
    async def nostupid(self, ctx):
        """This is a clear violation of the no stupid policy"""
        await ctx.send("https://cdn.discordapp.com/attachments/658726241288847361/1113893566075383818/image.png")

    @commands.command()
    async def gitpull(self, ctx):
        if ctx.author not in (self.bot.creator, self.bot.bernardo):
            raise commands.CheckFailure()
        message = await ctx.send("Pulling from git...")
        try:
            proc = await asyncio.create_subprocess_shell("git pull", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        except asyncio.TimeoutError:
            return await message.edit(content="Timed out while pulling from git.")
        resp = await proc.communicate()
        resp = "\n".join([x.decode('utf-8') for x in resp])
        if resp.startswith("Already up to date."):
            return await message.edit(content=f"```{resp}```")
        await message.edit(content=f"Commits pulled!\n```{resp}```")
        await proc.wait()
        await self.bot.session.close()
        await self.bot.close()

    @commands.group()
    @commands.has_any_role("Admin", "FlagBrew Team")
    async def wiki_thread(self, ctx):
        """Command handler for wiki thread top-level post. Will change the thread ID to ctx channel if no subcommand is passed"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Possible subcommands: `create_post`, `edit_post`, `add_item`, `delete_item`, `display`, and `raw_display`.")
            self.bot.persistent_vars_dict["wiki_thread"] = ctx.channel.id
            with open("saves/persistent_vars.json", "w") as file:
                json.dump(self.bot.persistent_vars_dict, file, indent=4)
            return await ctx.send(f"Successfully set the wiki thread to {ctx.channel.mention}.")

    @wiki_thread.command()
    async def create_post(self, ctx, *, content):
        """Creates the top level post in the wiki thread, pins it, and adds the message id to the persistent vars"""
        try:
            wiki_thread = ctx.guild.get_thread(self.bot.persistent_vars_dict["wiki_thread"])
        except Exception as e:
            return await ctx.send(f"An error occurred while trying to get the wiki thread. Please ensure the thread ID has been set via the top-level command.\n\n```{e}```")
        embed = discord.Embed(title="Wiki To-Do List", description=content)
        msg = await wiki_thread.send(embed=embed)
        await msg.pin()
        self.bot.persistent_vars_dict["wiki_post"] = msg.id
        with open("saves/persistent_vars.json", "w") as file:
            json.dump(self.bot.persistent_vars_dict, file, indent=4)
        
    @wiki_thread.command()
    @commands.has_any_role("Admin", "Bot Dev")
    async def edit_post(self, ctx, *, content):
        """Edits the top level post in the wiki thread. Required for removing items"""
        try:
            wiki_thread = ctx.guild.get_thread(self.bot.persistent_vars_dict["wiki_thread"])
            msg = await wiki_thread.fetch_message(self.bot.persistent_vars_dict["wiki_post"])
        except Exception as e:
            return await ctx.send(f"An error occurred while trying to get the wiki thread and message. Please ensure the thread ID has been set via the top-level command and there's a message set.\n\n```{e}```")
        embed = discord.Embed(title="Wiki To-Do List", description=content)
        await msg.edit(embed=embed)
        await ctx.send("Successfully edited the wiki post.", reference=msg)

    @wiki_thread.command()
    async def add_item(self, ctx, *, item):
        """Adds an individual item to the wiki thread"""
        try:
            wiki_thread = ctx.guild.get_thread(self.bot.persistent_vars_dict["wiki_thread"])
            msg = await wiki_thread.fetch_message(self.bot.persistent_vars_dict["wiki_post"])
        except Exception as e:
            return await ctx.send(f"An error occurred while trying to get the wiki thread and message. Please ensure the thread ID has been set via the top-level command and there's a message set.\n\n```{e}```")
        embed = msg.embeds[0]
        if not item.startswith("- "):
            embed.description += f"\n- {item}"
        else:
            embed.description += f"\n{item}"
        await msg.edit(embed=embed)
        await ctx.send("Successfully added the item to the wiki post.", reference=msg)
    
    @wiki_thread.command()
    async def delete_item(self, ctx, *, item):
        """Deletes an individual item from the wiki thread. Item must be an exact match, or the index of the item to delete"""
        try:
            wiki_thread = ctx.guild.get_thread(self.bot.persistent_vars_dict["wiki_thread"])
            msg = await wiki_thread.fetch_message(self.bot.persistent_vars_dict["wiki_post"])
        except Exception as e:
            return await ctx.send(f"An error occurred while trying to get the wiki thread and message. Please ensure the thread ID has been set via the top-level command and there's a message set.\n\n```{e}```")
        embed = msg.embeds[0]
        items = embed.description.split("\n")
        if item.isnumeric():
            removed = items.pop(int(item) - 1)
        elif f"- {item}" in items:
            items.remove(f"- {item}")
            removed = {item}
        else:
            return await ctx.send("The item you're trying to delete isn't there.")
        embed.description = "\n".join(items)
        await msg.edit(embed=embed)
        await ctx.send(f"Successfully removed the item {removed} from the wiki post.", reference=msg)

    @wiki_thread.command()
    async def display(self, ctx):
        """Displays the wiki thread's top-level post. Will not auto-update if the post is edited"""
        try:
            wiki_thread = ctx.guild.get_thread(self.bot.persistent_vars_dict["wiki_thread"])
            msg = await wiki_thread.fetch_message(self.bot.persistent_vars_dict["wiki_post"])
        except Exception as e:
            return await ctx.send(f"An error occurred while trying to get the wiki thread and message. Please ensure the thread ID has been set via the top-level command and there's a message set.\n\n```{e}```")
        await ctx.send(embed=msg.embeds[0])

    @wiki_thread.command()
    async def raw_display(self, ctx):
        """Displays the wiki thread's top-level post in raw text. Will not auto-update if the post is edited"""
        try:
            wiki_thread = ctx.guild.get_thread(self.bot.persistent_vars_dict["wiki_thread"])
            msg = await wiki_thread.fetch_message(self.bot.persistent_vars_dict["wiki_post"])
        except Exception as e:
            return await ctx.send(f"An error occurred while trying to get the wiki thread and message. Please ensure the thread ID has been set via the top-level command and there's a message set.\n\n```{e}```")
        await ctx.send(f"```{msg.embeds[0].description}```")

async def setup(bot):
    await bot.add_cog(Meta(bot))
