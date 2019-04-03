#!/usr/bin/env python3

import discord
from discord.ext import commands
import sys
import os

class Utility(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        print('Addon "{}" loaded'.format(self.__class__.__name__))
            
    @commands.has_permissions(ban_members=True) 
    @commands.command()
    async def restart(self, ctx):
        """Restarts the bot, obviously"""
        await ctx.send("Restarting...")
        with open("restart.txt", "w+") as f:
            f.write(str(ctx.message.channel.id))
            f.close()
        sys.exit(0)
        
    async def toggleroles(self, ctx, role, user):
        author_roles = user.roles[1:]
        if not role in author_roles:
            await user.add_roles(role)
            return False
        else:
            await user.remove_roles(role)
            return True
        
        
    @commands.command()
    async def togglerole(self, ctx, *, role=""):
        """Allows user to toggle update roles. You can use .masstoggle to apply all roles at once.
        Available roles: PKSM, Checkpoint, General"""
        await ctx.message.delete()
        user = ctx.message.author
        if not role:
            await ctx.send("You need to input a role to toggle! Do `.help togglerole` to see all available roles", delete_after=5)
            return  # prevents execution of the below try statement
        if role.lower() == "pksm":
            had_role = await self.toggleroles(ctx, self.bot.pksm_update_role, user)
            if had_role:
                info_string = "You will no longer be pinged for PKSM updates."
            else:
                info_string = "You will now receive pings for PKSM updates!"
        elif role.lower() == "checkpoint":
            had_role = await self.toggleroles(ctx, self.bot.checkpoint_update_role, user)
            if had_role:
                info_string = "You will no longer be pinged for Checkpoint updates."
            else:
                info_string = "You will now receive pings for Checkpoint updates!"        
        elif role.lower() == "general":
            had_role = await self.toggleroles(ctx, self.bot.general_update_role, user)
            if had_role:
                info_string = "You will no longer be pinged for general updates."
            else:
                info_string = "You will now recieve pings for general updates!"
        else:
            await ctx.send("Invalid entry! Do `.help togglerole` for available roles.", delete_after=5)
            return  # prevents execution of the below try statement

        # should only trigger if one of the role.lower() conditions is met
        try:
            await ctx.author.send(info_string)
        except discord.errors.Forbidden:
            await ctx.send(ctx.author.mention + ' ' + info_string, delete_after=5)
            
    @commands.command()
    async def masstoggle(self, ctx):
        """Allows a user to toggle all possible update roles. Use .help toggleroles to see possible roles."""
        await ctx.message.delete()
        user = ctx.message.author
        await self.toggleroles(ctx, self.bot.pksm_update_role, user)
        await self.toggleroles(ctx, self.bot.checkpoint_update_role, user)
        await self.toggleroles(ctx, self.bot.general_update_role, user)
        try:
            await user.send("Successfully toggled all possible roles.")
        except discord.errors.Forbidden:
            await ctx.send("{} Successfully toggled all possible roles.".format(ctx.author.mention), delete_after=5)
            
    @commands.command(aliases=['srm', 'mention'])
    @commands.has_any_role("Discord Moderator", "FlagBrew Team")
    async def secure_role_mention(self, ctx, update_role:str, channel:discord.TextChannel=None):
        """Securely mention a role. Options: pksm, checkpoint, general, votes, patrons, flagbrew. Can input a channel at the end for remote mentioning"""
        if not channel:
            channel = ctx.channel
        if update_role.lower() == "pksm":
            role = self.bot.pksm_update_role
        elif update_role.lower() == "checkpoint":
            role = self.bot.checkpoint_update_role
        elif update_role.lower() == "general":
            role = self.bot.general_update_role
        elif update_role.lower() == "votes":
            role = self.bot.patreon_votes_role
        elif update_role.lower() == "patrons":
            role = self.bot.patrons_role
        elif update_role.lower() == "flagbrew":
            role = self.bot.flagbrew_team_role
        else:
            return await ctx.send("You didn't give a valid role. Do `.help srm' to see all available roles.")
        try:
            await role.edit(mentionable=True, reason="{} wanted to mention users with this role.".format(ctx.author)) # Reason -> Helps pointing out folks that abuse this
        except:
            await role.edit(mentionable=True, reason="A staff member wanted to mention users with this role, and I couldn't log properly. Check {}.".format(self.bot.logs_channel.mention)) # Bypass the TypeError it kept throwing
        await channel.send("{}".format(role.mention))
        await role.edit(mentionable=False, reason="Making role unmentionable again.")
        try:
            await self.bot.logs_channel.send("{} pinged {} in {}".format(ctx.author, role.name, channel))
        except discord.Forbidden:
            pass # beta bot can't log

def setup(bot):
    bot.add_cog(Utility(bot))
