import discord
import json
import random
from datetime import datetime
from discord.ext import commands


class Warning(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if self.bot.is_mongodb:
            self.db = bot.db['flagbrew']
        print('Addon "{}" loaded'.format(self.__class__.__name__))

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def warn(self, ctx, target: discord.Member, *, reason="No reason was given"):
        """Warns a user. Kicks at 3 and 4 warnings, bans at 5"""
        try:
            self.bot.warns_dict[str(target.id)]
        except KeyError:
            self.bot.warns_dict[str(target.id)] = []
        self.bot.warns_dict[str(target.id)].append(
            {
                "reason": reason,
                "date": datetime.now().strftime("%D %H:%M:%S"),
                "warned_by": "{}".format(ctx.author),
        })
        warns = self.bot.warns_dict[str(target.id)]
        dm_msg = "You were warned on {}.\nThe reason provided was: `{}`.\nThis is warn #{}.".format(ctx.guild, reason, len(warns))
        log_msg = ""
        if len(warns) >= 5:
            dm_msg += "\nYou were banned for this warn. If you believe this was in error, please contact FlagBrew via email at `flagbrewinfo@gmail.com`."
            log_msg += "They were banned as a result of this warn."
        elif len(warns) >= 3:
            dm_msg += "\nYou were kicked for this warn. If you would like to rejoin the server, here is a permanent invite: https://discord.gg/bGKEyfY."
            if len(warns) == 4:
                dm_msg += "\nYou will be automatically banned if you are warned again."
            log_msg += "They were kicked as a result of this warn."
        elif len(warns) == 2:
            dm_msg += "You will be automatically kicked if you are warned again."
        embed = discord.Embed(title="{} warned".format(target))
        embed.description = "{} | {} was warned in {} by {} for `{}`. This is warn #{}. {}".format(target, target.id, ctx.channel.mention, ctx.author, reason, len(warns), log_msg)
        try:
            await target.send(dm_msg)
        except discord.Forbidden:
            embed.description += "\n**Could not DM user.**"
        if self.bot.is_mongodb:
            self.db['warns'].update_one(
                {
                    "user": str(target.id)
                },
                {
                    "$set": {
                        "user": str(target.id),
                        "warns": self.bot.warns_dict[str(target.id)]
                    }
                }, upsert=True)
        with open("saves/warns.json", "w") as f:
            json.dump(self.bot.warns_dict, f, indent=4)
        if len(warns) >= 5:
            embed = discord.Embed()
            img_choice = random.randint(1, 26)
            if img_choice in range(1, 13):  # ampharos
                embed.set_image(url="https://fm1337.com/static/img/ampharos-banned.jpg")
            if img_choice in range(13, 25):  # eevee
                embed.set_image(url="https://fm1337.com/static/img/eevee-banned.jpg")
            if img_choice in range(25, 27):  # giratina
                embed.set_image(url="https://fm1337.com/static/img/giratina-banned.jpg")
            await target.ban(reason="Warn #{}".format(len(warns)))
        elif len(warns) >= 3:
            await target.kick(reason="Warn #{}".format(len(warns)))
        try:
            await self.bot.logs_channel.send(embed=embed)
        except discord.Forbidden:
            pass  # beta can't log
        if len(warns) >= 5:
            return await ctx.send("Warned {}. This is warn #{}. {}".format(target, len(warns), log_msg), embed=embed)
        await ctx.send("Warned {}. This is warn #{}. {}".format(target, len(warns), log_msg))

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def delwarn(self, ctx, target: discord.Member, *, warn):
        """Deletes a users warn. Can take the warn number, or the warn reason"""
        try:
            warnings = len(self.bot.warns_dict[str(target.id)])
            if warnings == 0:
                return await ctx.send("{} doesn't have any warnings!".format(target))
        except KeyError:
            return await ctx.send("{} hasn't been warned before!".format(target))
        if warn.isdigit() and warn not in self.bot.warns_dict[str(target.id)]:
            try:
                warn = self.bot.warns_dict[str(target.id)].pop(int(warn) - 1)
            except (KeyError):
                return await ctx.send("{} doesn't have a warn with that number.".format(target))
        else:
            try:
                self.bot.warns_dict[str(target.id)].remove(warn)
            except ValueError:
                return await ctx.send("{} doesn't have a warn matching `{}`.".format(target, warn))
        if self.bot.is_mongodb:
            self.db['warns'].update_one(
                {
                    "user": str(target.id)
                },
                {
                    "$set": {
                        "user": str(target.id),
                        "warns": self.bot.warns_dict[str(target.id)]
                    }
                }, upsert=True)
        with open("saves/warns.json", "w") as f:
            json.dump(self.bot.warns_dict, f, indent=4)
        await ctx.send("Removed warn from {}.".format(target))
        warns_count = len(self.bot.warns_dict[str(target.id)])
        embed = discord.Embed(title="Warn removed from {}".format(target))
        embed.add_field(name="Warn Reason:", value=warn["reason"])
        embed.add_field(name="Warned By:", value=warn["warned_by"])
        if type(warn['date']) is float:  # Backwards compatibility
            warn_date = datetime.fromtimestamp(warn['date']).strftime("%D %H:%M:%S")
        else:
            warn_date = warn['date']
        embed.add_field(name="Warned On:", value=warn_date)
        embed.set_footer(text="{} now has {} warn(s).".format(target.name, warns_count))
        try:
            await target.send("Warn `{}` was removed on {}. You now have {} warn(s).".format(warn['reason'], ctx.guild, warns_count))
        except discord.Forbidden:
            embed.description += "\n**Could not DM user.**"
        try:
            await self.bot.logs_channel.send("{} had a warn removed:".format(target), embed=embed)
        except discord.Forbidden:
            pass  # beta can't log

    @commands.command()
    async def listwarns(self, ctx, target: discord.Member=None):
        """Allows a user to list their own warns, or a staff member to list a user's warns"""
        if not target or target == ctx.author:
            target = ctx.author
        elif target and self.bot.discord_moderator_role not in ctx.author.roles:
            raise commands.errors.CheckFailure()
            return
        try:
            warns = self.bot.warns_dict[str(target.id)]
        except KeyError:
            return await ctx.send("{} has no warns.".format(target))
        embed = discord.Embed(title="Warns for {}".format(target))
        count = 1
        for warn in warns:
            if type(warn['date']) is float:  # Backwards compatibility
                warn_date = datetime.fromtimestamp(warn['date']).strftime("%D %H:%M:%S")
            else:
                warn_date = warn['date']
            embed.add_field(name="Warn #{}".format(count), value="**Reason: {}**\n**Date: {}**".format(warn['reason'], warn_date))
            count += 1
        if count - 1 == 0:
            return await ctx.send("{} has no warns.".format(target))
        embed.set_footer(text="Total warns: {}".format(count-1))
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def clearwarns(self, ctx, target: discord.Member):
        """Clears all of a users warns"""
        try:
            warns = self.bot.warns_dict[str(target.id)]
            if len(warns) == 0:
                return await ctx.send("{} doesn't have any warnings!".format(target))
            self.bot.warns_dict[str(target.id)] = []
        except KeyError:
            return await ctx.send("{} already has no warns.".format(target))
        await ctx.send("Cleared warns for {}.".format(target))
        if self.bot.is_mongodb:
            self.db['warns'].update_one(
                {
                    "user": str(target.id)
                },
                {
                    "$set": {
                        "user": str(target.id),
                        "warns": self.bot.warns_dict[str(target.id)]
                    }
                }, upsert=True)
        with open("saves/warns.json", "w") as f:
            json.dump(self.bot.warns_dict, f, indent=4)
        embed = discord.Embed(title="Warns for {} cleared".format(target))
        embed.description = "{} | {} had their warns cleared by {}. Warns can be found below.".format(target, target.id, ctx.author)
        count = 1
        for warn in warns:
            if type(warn['date']) is float:  # Backwards compatibility
                warn_date = datetime.fromtimestamp(warn['date']).strftime("%D %H:%M:%S")
            else:
                warn_date = warn['date']
            embed.add_field(name="Warn #{}".format(count), value="Warned By: {}\nWarned On: {}\nReason: {}".format(warn['warned_by'], warn_date, warn['reason']))
            count += 1
        try:
            await target.send("All of your warns were cleared on {}.".format(ctx.guild))
        except discord.Forbidden:
            embed.description += "\n**Could not DM user.**"
        try:
            await self.bot.logs_channel.send(embed=embed)
        except discord.Forbidden:
            pass  # beta can't log

def setup(bot):
    bot.add_cog(Warning(bot))
