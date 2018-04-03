#!/usr/bin/env python3

import discord
from discord.ext import commands

class Events:

    def __init__(self, bot):
        self.bot = bot
        print('Addon "{}" loaded'.format(self.__class__.__name__))
        
        
    async def on_guild_join(self, guild):
        # Don't let the bot be used elsewhere with the same token
        if guild.id != 378420595190267915 and guild.id != 278222834633801728 and guild.id != 418291144850669569:
            try:
                await guild.owner.send("Left your server, `{}`, as this bot should only be used on the PKSM server under this token.".format(guild.name))
            except discord.Forbidden:
                for channel in guild.channels:
                   if guild.me.permissions_in(channel).send_messages and isinstance(channel, discord.TextChannel):
                        await channel.send("Left your server, as this bot should only be used on the PKSM server under this token.")
                        break
            finally:
                await guild.leave()
                
    async def on_member_join(self, member):
        embed = discord.Embed(title="New member!")
        embed.description = "{} | {}#{} | {}".format(member.mention, member.name, member.discriminator, member.id)
        if member.guild.id == 278222834633801728:
            await self.bot.logs_channel.send(embed=embed)
        elif member.guild.id == 418291144850669569:
            await member.guild.get_channel(418680841900785664).send(embed=embed)
        else:
            return
            
    async def on_member_remove(self, member):
        embed = discord.Embed(title="Member left :(")
        embed.description = "{} | {}#{} | {}".format(member.mention, member.name, member.discriminator, member.id)
        if member.guild.id == 278222834633801728:
            await self.bot.logs_channel.send(embed=embed)
        elif member.guild.id == 418291144850669569:
            await member.guild.get_channel(418680841900785664).send(embed=embed)
        else:
            return
                
                
    async def on_message(self, message):
        # auto ban on 15+ pings
        if len(message.mentions) > 15:
            embed = discord.Embed(description=message.content)
            await message.delete()
            await message.author.ban()
            await message.channel.send("{} was banned for attempting to spam user mentions.".format(message.author))
            
            
    async def on_message_delete(self, message):
        if isinstance(message.channel, discord.abc.GuildChannel) and message.author.id != self.bot.user.id:
            if message.channel != self.bot.logs_channel:
                embed = discord.Embed(description=message.content)
                if message.attachments:
                        attachment_urls = []
                        for attachment in message.attachments:
                            attachment_urls.append('[{}]({})'.format(attachment.filename, attachment.url))
                        attachment_msg = '\N{BULLET} ' + '\n\N{BULLET} s '.join(attachment_urls)
                        embed.add_field(name='Attachments', value=attachment_msg, inline=False)
                await self.bot.logs_channel.send("Message by {0} deleted in channel {1.mention}:".format(message.author, message.channel), embed=embed)
        
        
def setup(bot):
    bot.add_cog(Events(bot))