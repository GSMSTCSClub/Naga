import discord
from discord.ext import commands

import logging
import shutil
from pathlib import Path
from ruamel.yaml import YAML

def _get_cmd_prefix(bot: commands.Bot, msg: discord.Message) -> tuple[str]:
    """
    Gets the command prefix based off the guild of the message
    """
    def_prefix = bot.config["default_prefix"]
    guild_prefixes = bot.config["prefixes"]

    # if dm, use default prefix
    if msg.guild is None:
        return (def_prefix, )
    else:
        # if guild, use the guild's prefix, or if it doesn't exist, use the default
        return (guild_prefixes.get(msg.guild.id, def_prefix), )

DEFAULT_CONFIG_PATH = Path("config/default_config.yml")
CONFIG_PATH = Path("config/config.yml")

class CSClubBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        logging.basicConfig(level=logging.INFO, format='[%(name)s %(levelname)s] %(message)s')
        self.logger = logging.getLogger('bot')

        yml = YAML(typ='safe')

        # make cfg file if doesn't exist
        if not CONFIG_PATH.exists():
            shutil.copy(DEFAULT_CONFIG_PATH, CONFIG_PATH)
        # load cfg file
        with open(CONFIG_PATH) as cfg_file:
            self.config = yml.load(cfg_file)

        # do rest of init
        am = discord.AllowedMentions.none() # should not ever ping
        intents = discord.Intents.all()
        super().__init__(command_prefix=_get_cmd_prefix, allowed_mentions=am, intents=intents, *args, **kwargs)

    async def on_ready(self):
        self.logger.info(f'Connected to {self.user}')
        self.logger.info(f'Guilds  : {len(self.guilds)}')
        self.logger.info(f'Users   : {len(set(self.get_all_members()))}')
        self.logger.info(f'Channels: {len(list(self.get_all_channels()))}')

    def load_module(self, module: str):
        """
        Loads a module
        """
        try:
            self.load_extension(module)
        except Exception as e:
            self.logger.exception(f'Failed to load module {module}:')
            print("")
            self.logger.exception(e)
            print("")
        else:
            self.logger.info(f'Loaded module {module}.')

    def load_dir(self, directory: str):
        """
        Loads all modules in a directory
        """
        path = Path(directory)
        if not path.is_dir(): 
            self.logger.info(f"Directory {directory} does not exist, skipping")
            return

        modules = [f"{directory}.{p.stem}" for p in path.iterdir() if p.suffix == ".py"]
        for m in modules:
            self.load_module(m)

    def run(self, token):
        self.load_dir("core")
        self.load_dir("cogs")

        self.logger.info(f'Loaded {len(self.cogs)} cogs')
        super().run(token)

# this code is ran if this py script is called in terminal
# python3 bot.py
if __name__ == '__main__':

    # init bot, load token, activate discord
    bot = CSClubBot()
    token = open(bot.config['token_file'], 'r').read().split('\n')[0]
    bot.run(token)
