import discord
from discord.ext import commands
from collections.abc import Collection
import itertools

class CSClubBotHelp(commands.MinimalHelpCommand):

    ### BOT HELP ###

    async def send_bot_help(self, mapping):
        # force Misc at the end, sort rest by alphabetical
        cats = sorted(self.get_categories(), key=lambda k: (k == "Misc", k))

        self.paginator.add_line("**Categories:**")
        width = max([len(cat) for cat in cats]) + 2
        
        for left, right in zip(cats[0::2], cats[1::2]):
            self.paginator.add_line(f"`{left}`{' ' * int(2.3 * (width-len(left)))}`{right}`")
        if len(cats) % 2 == 1:
            self.paginator.add_line(f"`{cats[-1]}`")

        self.add_ending_note()
        await self.send_pages()

    def get_ending_note(self):
        return '`{0}{1} <command>` for in-depth help for a command\n' \
               '`{0}{1} <category>` for commands in a category\n' \
               .format(self.clean_prefix, self.invoked_with)

    def add_ending_note(self):
        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

    ### CATEGORY HELP ###

    async def send_category_help(self, cat):
        cogs = self.cogs_in_category(cat)
        cmds = [*itertools.chain.from_iterable(cog.get_commands() for cog in cogs)]

        # if category consists of one command and it's the same name, just redirect to there
        if len(cmds) == 1 and cat.lower() == str(cmds[0]).lower(): 
            if isinstance(cmds[0], commands.Group):
                return await self.send_group_help(cmds[0])
            else:
                return await self.send_command_help(cmds[0])

        self.paginator.add_line(f"**{cat} commands:**")
        
        # add authors
        authors = []
        for cog in cogs:
            authors += self.get_authors(cog)
        if authors:
            self.paginator.add_line("*Authored by* " + ", ".join(map(lambda a: a.mention, authors)))
        self.paginator.add_line()

        #self.add_desc(cog)
        self.add_subcommand_list(sorted(cmds, key=lambda c: c.name))

        self.add_ending_note()
        await self.send_pages()

    def add_subcommand_formatting(self, command, cell=0):
        # formats commands within groups (cmds w/ subcommands) or categories
        ctext = f"{self.clean_prefix}{command}".ljust(cell)
        fmt = '`{0}` {1}' if command.short_doc else '`{}`'
        self.paginator.add_line(fmt.format(ctext, command.short_doc))

    def add_subcommand_list(self, cmds: "Collection[commands.Command]"):
        """
        Adds a formatted list of subcommands to the paginator
        """
        if len(cmds) > 0:
            # length of largest command
            maxlen = max(len(str(cmd)) + 1 for cmd in cmds)
            
            for command in cmds:
                self.add_subcommand_formatting(command, maxlen)

    ### CATEGORY UTIL ###

    def get_categories(self) -> "set[str]":
        """
        List of every category name out of the registered cogs in the bot.
        """
        return set(self.category_name(cog) for cog in self.context.bot.cogs.values())
    
    def category_name(self, cog: commands.Cog) -> str:
        """
        Normally, the category name is just the qualified name of the cog, but it can be overrided
        by adding a HELP_CATEGORY attribute. Multiple cogs with the same category will be merged into 
        one category in help.
        """
        if hasattr(cog, "HELP_CATEGORY"): return cog.HELP_CATEGORY
        else: return cog.qualified_name

    def cogs_in_category(self, cat: str) -> "tuple[commands.Cog]":
        """
        Gets all registered cogs that have the specified category name
        """
        cogs = self.context.bot.cogs.values()
        return tuple(cog for cog in cogs if self.category_name(cog) == cat)

    ### AUTHOR UTIL ###

    def get_authors(self, c: "commands.Command | commands.Cog") -> "tuple[discord.User]":
        authors = []

        if isinstance(c, commands.Cog):
            if hasattr(c, "AUTHORS"): pot_authors = c.AUTHORS
            elif hasattr(c, "AUTHOR"): pot_authors = c.AUTHOR
            else: pot_authors = []

            if isinstance(pot_authors, int): authors.append(pot_authors)
            elif isinstance(pot_authors, Collection): authors.extend(pot_authors)
        
        elif isinstance(c, commands.Command):
            authors.extend(a.id for a in self.get_authors(c.cog)) # TODO cmd author sys

        auth_users = [self.context.bot.get_user(aid) for aid in authors if isinstance(aid, int)]
        return tuple(filter(lambda u: u is not None, auth_users))

    ### COMMAND/GROUP HELP ###

    async def send_command_help(self, command):
        self.add_command_heading(command)
        self.add_description(command)

        self.paginator.add_line()
        self.paginator.add_line("**Usage:**")
        # main signature
        self.paginator.add_line(f"`{self.clean_prefix}{command} {command.signature}`") # TODO reimpl custom defined signatures in a clean way
        # any subcommands if they exist
        # ordered by how they're defined within the cog class itself
        if isinstance(command, commands.Group):
            self.add_subcommand_list(command.all_commands.values())
        self.paginator.add_line()

        # add line for aliases (if present)
        aliases = []
        for alias in command.aliases:
            parent = command.full_parent_name
            if parent:
                aliases.append(f"{self.clean_prefix}{parent} {alias}")
            else:
                aliases.append(f"{self.clean_prefix}{alias}")
        if aliases:
            self.paginator.add_line(f"**Aliases:** {', '.join(map(discord.utils.escape_markdown, aliases))}", empty=True)
        
        # add authors
        authors = self.get_authors(command)
        if authors:
            self.paginator.add_line("*Authored by* " + ", ".join(map(lambda a: a.mention, authors)))

        self.paginator.close_page()
        await self.send_pages()

    def add_command_heading(self, command: commands.Command):
        """
        Adds a heading of the current command
        """
        parent = command.full_parent_name
        full_cmd = command.name if not parent else parent + ' ' + command.name
        self.paginator.add_line(f"Help for `{self.clean_prefix}{full_cmd}`:")

    def add_description(self, c: "commands.Command | commands.Cog"):
        """
        Adds a description of the current command (or cog)
        This is usually the docstring (this thing right here) of the function that makes the command
        """
        if hasattr(c, "help"): desc = c.help
        elif hasattr(c, "description"): desc = c.description
        else: desc = None

        if desc:
            try:
                self.paginator.add_line(desc.strip())
            except RuntimeError:
                for line in desc.splitlines():
                    self.paginator.add_line(line)
                self.paginator.add_line()

    ### MISC ###

    async def send_pages(self):
        """
        A helper utility to send the page output from :attr:`paginator` to the destination.
        """

        # copied from d.py

        destination = self.get_destination()
        for page in self.paginator.pages:
            # make sure it does NOT ping anyone ever
            await destination.send(page, allowed_mentions=discord.AllowedMentions.none())

    ### UHHHHHH, JUST DON'T LOOK AT THIS ###

    async def command_callback(self, ctx, *, command=None):
        """|coro|

        The actual implementation of the help command.

        It is not recommended to override this method and instead change
        the behaviour through the methods that actually get dispatched.

        - :meth:`send_bot_help`
        - :meth:`send_category_help` (*replaces `send_cog_help`)
        - :meth:`send_command_help`
        - :meth:`get_destination`
        - :meth:`command_not_found`
        - :meth:`subcommand_not_found`
        - :meth:`send_error_message`
        - :meth:`on_help_command_error`
        - :meth:`prepare_help_command`
        """
        # this method is mainly copied from discord.py
        # however because discord.py's default "search by cog" kinda thing is not 
        # completely compatible with the category system, this fn needs to be modified


        await self.prepare_help_command(ctx, command)
        bot: commands.Bot = ctx.bot

        if command is None:
            mapping = self.get_bot_mapping()
            return await self.send_bot_help(mapping)

        maybe_coro = discord.utils.maybe_coroutine

        # *Check for command first
        # Since we want to have detailed errors when someone
        # passes an invalid subcommand, we need to walk through
        # the command group chain ourselves.
        keys = command.split(' ')
        cmd = bot.all_commands.get(keys[0])
        if cmd is None:
            # *If it's not a command, check it's a category
            cat_match = next((c for c in self.get_categories() if c.lower() == command.lower()), None)

            if cat_match is not None:
                return await self.send_category_help(cat_match)

            # *If not a category, just raise the cmd not found err
            string = await maybe_coro(self.command_not_found, self.remove_mentions(keys[0]))
            return await self.send_error_message(string)

        # Subcommand check
        for key in keys[1:]:
            try:
                found = cmd.all_commands.get(key)
            except AttributeError:
                string = await maybe_coro(self.subcommand_not_found, cmd, self.remove_mentions(key))
                return await self.send_error_message(string)
            else:
                if found is None:
                    string = await maybe_coro(self.subcommand_not_found, cmd, self.remove_mentions(key))
                    return await self.send_error_message(string)
                cmd = found

        # *both cmds & groups will be handled by the same cmd so no need for send_group_help
        return await self.send_command_help(cmd)

class Help(commands.Cog):
    HELP_CATEGORY = "Misc"
    AUTHORS = (141294044671246337,)

async def setup(bot):
    helpcog = Help()
    await bot.add_cog(helpcog)
    bot.help_command = CSClubBotHelp()
    bot.help_command.cog = helpcog
