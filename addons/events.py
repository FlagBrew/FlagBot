#!/usr/bin/env python3

import discord
import requests
import secrets
import qrcode
import io
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
                if not message.content:
                    return
                embed = discord.Embed(description=message.content)
                try:
                    await self.bot.logs_channel.send("Message by {0} deleted in channel {1.mention}:".format(message.author, message.channel), embed=embed)
                except discord.Forbidden:
                    pass  # beta bot can't log

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles and ((self.bot.patrons_role in after.roles and self.bot.patrons_role not in before.roles) or
                                            (self.bot.patrons_role in before.roles and self.bot.patrons_role not in after.roles)):
            token = secrets.token_urlsafe(16)
            data = {
                "secret": self.bot.site_secret,
                "user_id": str(before.id)
            }
            if len(before.roles) < len(after.roles):
                await self.bot.patrons_channel.send("Welcome to the super secret cool kids club {}!"
                                                    " You can find up to date PKSM builds in <#531117773754073128>, and all patron news will be role pinged in <#330065133978255360>.".format(after.mention))
                url = "https://flagbrew.org/patron/generate"
                data["token"] = token
                message = ("Congrats on becoming a patron! You can add the token below to PKSM's config to access some special patron only stuff. It's only valid until your"
                           " patron status is cancelled, so keep up those payments!"
                           " To access the hidden Patron settings menu, press the four corners of the touch screen while on the configuration screen."
                           " If you need any further help setting it up, ask in {}!\n\n`{}`".format(self.bot.patrons_channel.mention, token))
                qr = qrcode.QRCode(version=None)
                qr.add_data(token)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                bytes = io.BytesIO()
                img.save(bytes, format='PNG')
                bytes = bytes.getvalue()
                f = discord.File(io.BytesIO(bytes), filename="qr.png")
            else:
                message = ("Unfortunately, your patreon subscription has been cancelled, or stopped renewing automatically. This means your token, and the special features,"
                           " have all expired. If you do end up renewing your subscription at a later date, you will recieve a new token.")
                url = "https://flagbrew.org/patron/remove"
                f = None
            requests.post(url, data=data)
            try:
                await before.send(message, file=f)
            except discord.Forbidden:
                if len(before.roles) < len(after.roles):
                    await self.bot.fetch_user(211923158423306243).send("Could not send token `{}` to user {}.".format(token, before))
                else:
                    await self.bot.fetch_user(211923158423306243).send("Could not notify user {} of token expiration.".format(before))


def setup(bot):
    bot.add_cog(Events(bot))
