import discord
from discord.ext import commands

import io
import traceback

async def on_command_error(ctx: commands.Context, exc: Exception):
    if isinstance(exc, commands.CommandInvokeError):
        if isinstance(exc.original, discord.Forbidden):
            try: 
                await ctx.send(f'Permissions error: `{exc}`', delete_after=10)
            except discord.Forbidden:
                pass
            return
        await notify_devs(ctx, exc.original)

    elif isinstance(exc, commands.CheckFailure):
        await ctx.send("You can't do that. " + str(exc), delete_after=10)

    elif isinstance(exc, commands.CommandNotFound):
        pass

    elif isinstance(exc, commands.ConversionError):
        await ctx.send(f"Expected a {exc.converter.__name__}", delete_after=10)

    elif isinstance(exc, commands.BadArgument):
        await ctx.send(''.join(exc.args) or 'Bad argument. No further information was specified.', delete_after=10)

    elif isinstance(exc, commands.UserInputError):
        if hasattr(exc, "message") and exc.message:
            await ctx.send(exc.message, delete_after=10)
        else:
            await ctx.send(f'Error: {" ".join(exc.args)}', delete_after=10)
    
    elif isinstance(exc, commands.CommandOnCooldown):
        await ctx.send(f":snowflake: Please wait {exc.retry_after} seconds to use this command again.")
    
    else:
        await notify_devs(ctx, exc)

async def notify_devs(ctx, exc):
    bot = ctx.bot

    simple_info = "".join(traceback.format_exception_only(type(exc), exc)).strip()
    info = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__, chain=False))
    bot.logger.error(info)

    exc_file = discord.File(io.StringIO(info), 'traceback.txt')

    cmd = ctx.command
    cog = ctx.cog

    if cmd is None or cog is None:
        await ctx.send(f'{simple_info}, something happened, one of the devs should check the logs.', file=exc_file)
        return

    devids = []
    if hasattr(cmd.callback, 'devids'):
        cmd_devids = cmd.callback.devids
        devids += [cmd_devids] if isinstance(cmd_devids, int) else cmd_devids
    if hasattr(cog, 'devids'):
        cog_devids = cog.devids
        devids += [cog_devids] if isinstance(cog_devids, int) else cog_devids
    
    devids = set(devids)

    if len(devids) == 0:
        await ctx.send(f'{simple_info}. btw the creator of this command is a coward.', file=exc_file)
        return

    devs = []
    for devid in devids:
        dev = await ctx.bot.fetch_user(devid)
        if dev is not None: devs.append(dev.name)
    
    if devs:
        insert = "one of " if len(devs) > 1 else ""
        await ctx.send(f'{simple_info}. You should probably inform {insert}{", ".join(devs)}.', file=exc_file)
    else:
        await ctx.send(f'{simple_info}, but I couldn\'t find the creator of this command.', file=exc_file)

def setup(bot: commands.Bot):
    bot.add_listener(on_command_error)