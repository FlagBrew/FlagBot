import discord
from discord.ext import commands

class Count:

    def __init__(self, bot):
        self.bot = bot
        print('Addon "{}" loaded'.format(self.__class__.__name__))
        
    @commands.command()
    @commands.cooldown(rate=1, per=210.0, type=commands.BucketType.channel)
    async def wait(self, ctx):
        """Returns how long it's gonna take"""
        if not ctx.channel.id == 379201279479513100 and ctx.guild.id == 278222834633801728:
            await ctx.message.delete()
            ctx.command.reset_cooldown(ctx)
            try:
                return await ctx.author.send("This command is restricted to <#379201279479513100>. Please try again there.")
            except:
                return await ctx.send("This command is restricted to <#379201279479513100>. Please try again there.")
        with open("tally.txt") as f:
            tally = f.read()
        await ctx.send("It's gonna be **{}** more {} till Ultra Sun and Ultra Moon is supported :slight_smile:".format(tally, "weeks" if tally != 1 else "week"))
            
    @commands.command()
    async def modify(self, ctx, amount=0):
        """Modify the timer"""
        if ctx.author == ctx.guild.owner or ctx.author.name == "bernardogiordano":
            with open("tally.txt") as f:
                tally = f.read()
                f.close()
            if amount == 0:
                return await ctx.send("No change was made to the wait. It's still at {} {} :frowning2:".format(tally, "week" if tally == 1 else "weeks"))
            elif int(tally) + amount <= 0:
                return await ctx.send("Error, you're going into a bad place!")
            else:
                with open("tally.txt", "w") as f:
                    tally = int(tally) + amount
                    f.write(str(tally))
                    f.close()
            if amount < 0:
                true_amount = amount - amount - amount
                await ctx.send("Removed {} {} from the wait. It will now be **{}** {} until Ultra Sun and Ultra Moon is supported :slight_frown:".format(true_amount, "weeks" if true_amount != 1 else "week", tally, "week" if tally == 1 else "weeks"))
            else:
                await ctx.send("Added {} {} to the wait. It will now be **{}** weeks until Ultra Sun and Ultra Moon is supported :slight_smile:".format(amount, "weeks" if amount != 1 else "week", tally))
        else:
            await ctx.send("You don't have permission to do that!")
            
def setup(bot):
    bot.add_cog(Count(bot))
