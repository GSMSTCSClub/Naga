import discord
from discord.ext import commands

import git
import importlib
import sys

REPO = git.Repo() # this repo

class Developer(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        # if member has a developer role
        roles = self.bot.config["dev_roles"].get(ctx.guild.id)
        if roles is not None and any(r.id in roles for r in ctx.author.roles):
            return True

        # if member has manage role or admin
        perms: discord.Permissions = ctx.author.guild_permissions
        if perms.manage_roles or perms.administrator:
            return True

        # if member is the bot creator
        return await self.bot.is_owner(ctx.author)

    @commands.command(aliases=['git_pull'])
    async def update(self, ctx, *, ext=None):
        """
        Updates the bot from the GitHub repo
        """

        await ctx.send(':warning: Warning! Pulling from Git!')
        await ctx.send(f'`Git` response: ```diff\n{REPO.git.pull()}```')
        if ext:
            await self.reload(ctx, ext=ext)

    @commands.group(invoke_without_command=True)
    async def reload(self, ctx, *, ext):
        """
        Reloads an extension
        """
        logger = self.bot.logger

        if "." not in ext: ext = "cogs." + ext
        logger.info("Reloading %s", ext)
        try:
            ctx.bot.reload_extension(ext)
        except commands.ExtensionNotLoaded:
            await self.load(ctx, ext=ext)
        except Exception as e:
            await ctx.send(f'Failed to load: `{ext}`\n```py\n{e}\n```')
            logger.error("Error while reloading %s", ext, exc_info=e)
        else:
            logger.info("Reloaded %s!", ext)
            print()
            await ctx.send(f'\N{OK HAND SIGN} Reloaded extension `{ext}` successfully')

    @commands.command()
    async def load(self, ctx, *, ext):
        """
        Loads an extension
        """
        logger = self.bot.logger

        logger.info("Loading %s", ext)
        try:
            ctx.bot.load_extension(ext)
        except Exception as e:
            await ctx.send(f'Failed to load: `{ext}`\n```py\n{e}\n```')
            logger.error("Error while loading %s", ext, exc_info=e)
        else:            
            logger.info("Loaded %s!", ext)
            print()
            await ctx.send(f'\N{OK HAND SIGN} **Loaded** extension `{ext}` successfully')

    @commands.command()
    async def unload(self, ctx, *, ext):
        """
        Unloads an extension
        """
        logger = self.bot.logger

        logger.info("Unloading %s", ext)
        try:
            ctx.bot.unload_extension(ext)
        except Exception as e:
            await ctx.send(f'Failed to unload: `{ext}`\n```py\n{e}\n```')
            logger.error("Error while unloading %s", ext, exc_info=e)
        else:
            logger.info("Unloaded %s!", ext)
            print()
            await ctx.send(f'\N{OK HAND SIGN} **Unloaded** extension `{ext}` successfully')

    @reload.command(name='all', invoke_without_command=True)
    async def reload_all(self, ctx):
        """
        Reloads all extensions
        """

        logger = self.bot.logger
        
        logger.info("Reloading all extensions")
        for ext in ctx.bot.extensions.copy():
            try:
                logger.info("Reloading %s", ext)
                ctx.bot.reload_extension(ext)
                logger.info("Reloaded %s!", ext)
            except Exception as e:
                await ctx.send(f'Failed to load `{ext}`:\n```py\n{e}\n```')
                logger.error("Error while reloading %s", ext, exc_info=e)

        await ctx.send(f'\N{OK HAND SIGN} Reloaded {len(ctx.bot.extensions)} extensions successfully')

    @commands.command()
    @commands.is_owner()
    async def die(self, ctx):
        """
        Kill the bot and restarts it. For real it kills the bot don't spam this please
        """
        await ctx.send(r"\*pop\*")
        await self.bot.logout()

    @commands.command()
    async def version(self, ctx):
        """
        Prints important version information about the bot's Python and discord.py installation
        """
        lines = (
            f"Python {sys.version}",
            "",
            f"discord.py version: {discord.__version__}"
        )

        await ctx.send("\n".join(lines))
    
def setup(bot):
    bot.add_cog(Developer(bot))
