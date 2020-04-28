import discord
from discord import Member
from discord.ext import commands
from discord.ext.commands import Context, CommandError

from tourminator.bot import TourminatorBot


class NotRegisteredError(CommandError):
    def __init__(self, ctx: Context):
        super().__init__('{0.name}, you are not registered!\n'
                         'Please use `{1}register` to register on this bot.'.format(ctx.author, ctx.cog.bot.command_prefix))


async def is_registered(ctx: Context):
    if not ctx.cog.bot.db.is_registered(ctx.author.id, ctx.author.guild.id):
        raise NotRegisteredError(ctx)
    return True


class UserManagementCog(commands.Cog, name='User Management'):
    def __init__(self, bot: TourminatorBot):
        self.bot = bot

    def cog_check(self, ctx):
        return hasattr(ctx.author, 'guild')

    @commands.command()
    async def register(self, ctx: Context):
        """Register to the bot on this server, to be able to participate in events"""
        member: Member = ctx.author

        self.bot.db.register_guild(member.guild.id)
        message = '{0.name}, you are registered now!'.format(member) \
            if self.bot.db.register_user(member.id, member.guild.id) \
            else '{0.name}, you are already registered.'.format(member)

        await ctx.send(message)

    @commands.command()
    @commands.check(is_registered)
    async def check_registered(self, ctx: Context):
        await ctx.send('Yes')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, NotRegisteredError):
            await ctx.send(str(error))
