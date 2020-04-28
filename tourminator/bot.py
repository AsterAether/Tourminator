from discord.ext import commands

from tourminator.db import DatabaseService


class TourminatorBot(commands.Bot):

    def __init__(self, command_prefix, db_file):
        super().__init__(command_prefix)

        self.db = DatabaseService(db_file)

        from tourminator import cogs
        self.add_cog(cogs.UserManagementCog(self))

    async def on_ready(self):
        print('Online as {0.user}'.format(self))
