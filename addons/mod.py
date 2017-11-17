#!/usr/bin/env python3

import discord
from discord.ext import commands
import os
import sys
import json
import asyncio

class Moderation:
    """Bot commands for moderation."""
    def __init__(self, bot):
        self.bot = bot
        print('Addon "{}" loaded'.format(self.__class__.__name__))
        
    def find_user(self, user, ctx):
        found_member = self.bot.guild.get_member(user)
        if not found_member:
            found_member = self.bot.guild.get_member_named(user)
        if not found_member:
            try:
                found_member = ctx.message.mentions[0]
            except IndexError:
                pass
        if not found_member:
            return None
        else:
            return found_member
    
    @commands.has_permissions(kick_members=True)    
    @commands.command(pass_context=True)
    async def kick(self, ctx, member, *, reason="No reason was given."):
        """Kick a member."""
        found_member = self.find_user(member, ctx)
        if found_member == ctx.message.author:
            return await ctx.send("You can't kick yourself, obviously")
        elif not found_member:
            await ctx.send("That user could not be found.")
        else:
            await found_member.kick(reason=reason)
            await ctx.send("Successfully kicked user {0.name}#{0.discriminator}!".format(found_member))
    
    @commands.has_permissions(ban_members=True)    
    @commands.command(pass_context=True)
    async def ban(self, ctx, member, *, reason="No reason was given."):
        """Ban a member."""
        found_member = self.find_user(member, ctx)
        if found_member == ctx.message.author:
            return await ctx.send("You can't ban yourself, obviously")
        if not found_member:
            await ctx.send("That user could not be found.")
        else:
            await self.bot.guild.ban(found_member, delete_message_days=0, reason=reason)
            await ctx.send("Successfully banned user {0.name}#{0.discriminator}!".format(found_member))
            
def setup(bot):
    bot.add_cog(Moderation(bot))
