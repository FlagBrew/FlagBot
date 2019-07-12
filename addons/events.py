#!/usr/bin/env python3

import discord
from discord.ext import commands
from datetime import datetime


class Events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        print('Addon "{}" loaded'.format(self.__class__.__name__))

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        # Don't let the bot be used elsewhere with the same token
        if guild.id != self.bot.testing_id and guild.id != self.bot.flagbrew_id:
            try:
                await guild.owner.send("Left your server, `{}`, as this bot should only be used on the PKSM server under this token.".format(guild.name))
            except discord.Forbidden:
                for channel in guild.channels:
                    if guild.me.permissions_in(channel).send_messages and isinstance(channel, discord.TextChannel):
                        await channel.send("Left your server, as this bot should only be used on the PKSM server under this token.")
                        break
            finally:
                await guild.leave()

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        async for ban in guild.audit_logs(limit=20, action=discord.AuditLogAction.ban):  # 20 to handle multiple staff bans in quick succession
            if ban.target == user:
                if ban.reason:
                    reason = ban.reason
                else:
                    reason = "No reason was given. Please do that in the future!"
                admin = ban.user
                break
            else:
                return
        embed = discord.Embed(title="{} banned".format(user))
        embed.description = "{} was banned by {} for:\n\n{}".format(user, admin, reason)
        try:
            await self.bot.logs_channel.send(embed=embed)
        except discord.Forbidden:
            pass  # beta bot can't log

    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(title="New member!")
        embed.description = "{} | {}#{} | {}".format(member.mention, member.name, member.discriminator, member.id)
        if (datetime.now() - member.created_at).days < 1:
            embed.description += "\n**Account was created {} days ago.".format((datetime.now() - member.created_at).days)
        if member.guild.id == self.bot.flagbrew_id:
            try:
                await self.bot.logs_channel.send(embed=embed)
            except discord.Forbidden:
                pass  # beta bot can't log

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        embed = discord.Embed(title="Member left :(")
        embed.description = "{} | {}#{} | {}".format(member.mention, member.name, member.discriminator, member.id)
        if member.guild.id == self.bot.flagbrew_id:
            try:
                await self.bot.logs_channel.send(embed=embed)
            except discord.Forbidden:
                pass  # beta bot can't log

    @commands.Cog.listener()
    async def on_message(self, message):
        # auto ban on 15+ pings
        if len(message.mentions) > 15:
            embed = discord.Embed(description=message.content)
            await message.delete()
            await message.author.ban()
            await message.channel.send("{} was banned for attempting to spam user mentions.".format(message.author))

        # Watch hook for susp account(s)
        if message.author.id == 592144464382787595:
            embed = discord.Embed(description=message.content)
            await self.bot.logs_channel.send("Suspicious user `{}` sent a message:".format(message.author), embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if isinstance(message.channel, discord.abc.GuildChannel) and message.author.id != self.bot.user.id and message.guild.id == self.bot.flagbrew_id:
            if message.channel != self.bot.logs_channel:
                embed = discord.Embed(description=message.content)
                if message.attachments:
                        attachment_urls = []
                        for attachment in message.attachments:
                            attachment_urls.append('[{}]({})'.format(attachment.filename, attachment.url))
                        attachment_msg = '\N{BULLET} ' + '\n\N{BULLET} s '.join(attachment_urls)
                        embed.add_field(name='Attachments', value=attachment_msg, inline=False)
                try:
                    await self.bot.logs_channel.send("Message by {0} deleted in channel {1.mention}:".format(message.author, message.channel), embed=embed)
                except discord.Forbidden:
                    pass  # beta bot can't log

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles and ((self.bot.patrons_role in after.roles and self.bot.patrons_role not in before.roles) or
                                            (self.bot.patrons_role in before.roles and self.bot.patrons_role not in after.roles)):
            if len(before.roles) < len(after.roles):
                await self.bot.patrons_channel.send("Welcome to the super secret cool kids club {}! You can find up to date PKSM builds in <#531117773754073128>, and all patron news will be role pinged in <#330065133978255360>.".format(after.mention))
            else:
                # await self.bot.patrons_channel.send("How sad, {} has betrayed us and stopped giving our gods money :(".format(after))
                # Commented out until Bernardo approves of a leaving message
                pass


def setup(bot):
    bot.add_cog(Events(bot))
