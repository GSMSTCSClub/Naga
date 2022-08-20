import discord
from discord.ext import commands

import git
import sys
from enum import IntEnum
from itertools import groupby, chain

REPO = git.Repo() # this repo

class ExtStatus(IntEnum):
    LOAD_SUCCESS = 0,
    LOAD_FAIL = 1,
    RELOAD_SUCCESS = 2,
    RELOAD_FAIL = 3,
    UNLOAD_SUCCESS = 4,
    UNLOAD_FAIL = 5

class Developer(commands.Cog):
    AUTHORS = (141294044671246337, )

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

    async def reload_ext(self, ext) -> "tuple[ExtStatus, str, Exception | None]":
        logger = self.bot.logger
        
        if "." not in ext: ext = "cogs." + ext
        logger.info("Reloading %s", ext)
        try:
            await self.bot.reload_extension(ext)
        except commands.ExtensionNotLoaded:
            return await self.load_ext(ext)
        except Exception as e:
            logger.error("Error while reloading %s", ext, exc_info=e)
            return (ExtStatus.RELOAD_FAIL, ext, e)

        logger.info("Reloaded %s!", ext)
        return (ExtStatus.RELOAD_SUCCESS, ext, None)

    async def load_ext(self, ext) -> "tuple[ExtStatus, str, Exception | None]":
        logger = self.bot.logger
        
        if "." not in ext: ext = "cogs." + ext
        logger.info("Loading %s", ext)
        try:
            await self.bot.load_extension(ext)
        except Exception as e:
            logger.error("Error while loading %s", ext, exc_info=e)
            return (ExtStatus.LOAD_FAIL, ext, e)

        logger.info("Loaded %s!", ext)
        return (ExtStatus.LOAD_SUCCESS, ext, None)
    
    async def unload_ext(self, ext) -> "tuple[ExtStatus, str, Exception | None]":
        logger = self.bot.logger

        if "." not in ext: ext = "cogs." + ext
        logger.info("Unloading %s", ext)
        try:
            await self.bot.unload_extension(ext)
        except Exception as e:
            logger.error("Error while unloading %s", ext, exc_info=e)
            return (ExtStatus.UNLOAD_FAIL, ext, e)

        logger.info("Unloaded %s!", ext)
        return (ExtStatus.UNLOAD_SUCCESS, ext, None)

    @commands.group(invoke_without_command=True)
    async def reload(self, ctx, *ext):
        """
        Reloads extensions
        """

        attempts = [await self.reload_ext(e) for e in ext]
        attempts = sorted(attempts, key=lambda t: t[0])
        statuses = dict((k, tuple(g)) for k, g in groupby(attempts, key=lambda t: t[0]))
        rs, rf, ls, lf = \
            statuses.get(ExtStatus.RELOAD_SUCCESS, ()),\
            statuses.get(ExtStatus.RELOAD_FAIL, ()),\
            statuses.get(ExtStatus.LOAD_SUCCESS, ()),\
            statuses.get(ExtStatus.LOAD_FAIL, ())

        msg_lines = []
        if len(rs) > 0: msg_lines.append(
            '\N{OK HAND SIGN} Reloaded extension{} {} successfully'.format(
                "s" if len(rs) != 1 else "",
                ", ".join(f"`{name}`" for _, name, _ in rs)
            )
        )
        if len(ls) > 0: msg_lines.append(
            '\N{OK HAND SIGN} Loaded extension{} {} successfully'.format(
                "s" if len(ls) != 1 else "",
                ", ".join(f"`{name}`" for _, name, _ in ls)
            )
        )

        if len(msg_lines) > 0: msg_lines.append("")

        for _, name, e in chain(rf, lf):
            msg_lines.append(f"Failed to load: `{name}`\n```py\n{e}\n```")

        await ctx.send('\n'.join(msg_lines))

    @commands.command()
    async def load(self, ctx, *ext):
        """
        Loads extensions
        """

        attempts = [await self.load_ext(e) for e in ext]
        attempts = sorted(attempts, key=lambda t: t[0])
        statuses = dict((k, tuple(g)) for k, g in groupby(attempts, key=lambda t: t[0]))

        ls, lf = \
            statuses.get(ExtStatus.LOAD_SUCCESS, ()),\
            statuses.get(ExtStatus.LOAD_FAIL, ())

        msg_lines = []
        if len(ls) > 0: msg_lines.append(
            '\N{OK HAND SIGN} Loaded extension{} {} successfully'.format(
                "s" if len(ls) != 1 else "",
                ", ".join(f"`{name}`" for _, name, _ in ls)
            )
        )

        if len(msg_lines) > 0: msg_lines.append("")

        for _, name, e in lf:
            msg_lines.append(f"Failed to load: `{name}`\n```py\n{e}\n```")

        await ctx.send('\n'.join(msg_lines))

    @commands.command()
    async def unload(self, ctx, *ext):
        """
        Unloads extensions
        """

        attempts = [await self.unload_ext(e) for e in ext]
        attempts = sorted(attempts, key=lambda t: t[0])
        statuses = dict((k, tuple(g)) for k, g in groupby(attempts, key=lambda t: t[0]))
        us, uf = \
            statuses.get(ExtStatus.UNLOAD_SUCCESS, ()),\
            statuses.get(ExtStatus.UNLOAD_FAIL, ())

        msg_lines = []
        if len(us) > 0: msg_lines.append(
            '\N{OK HAND SIGN} Unloaded extension{} {} successfully'.format(
                "s" if len(us) != 1 else "",
                ", ".join(f"`{name}`" for _, name, _ in us)
            )
        )

        if len(msg_lines) > 0: msg_lines.append("")

        for _, name, e in uf:
            msg_lines.append(f"Failed to unload: `{name}`\n```py\n{e}\n```")

        await ctx.send('\n'.join(msg_lines))

    @reload.command(name='all', invoke_without_command=True)
    async def reload_all(self, ctx):
        """
        Reloads all extensions
        """

        return await self.reload(ctx, *ctx.bot.extensions)

    @commands.command()
    @commands.is_owner()
    async def die(self, ctx):
        """
        Kills the bot and restarts it. For real it kills the bot don't spam this please
        """
        await ctx.send(r"\*pop\*")
        await self.bot.close()

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
    
    @commands.command()
    async def crash(self, ctx):
        """
        Causes an error.
        """
        raise Exception(f"{ctx.prefix}crash induced error")

async def setup(bot):
    await bot.add_cog(Developer(bot))
