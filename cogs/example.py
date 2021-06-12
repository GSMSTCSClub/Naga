# this cog is an example of how cogs should be set up

# imports, these two should always be imported, there may be more here (sometimes much more) 
# if you're using a lot of libraries. feel free to ask @Endr#2382 to install a library!
import discord
from discord.ext import commands

import random

# the class name should be the name of the category
# it should extend the commands.Cog class
class Example(commands.Cog):

    # the init should always have at least a bot parameter.
    # the bot parameter needs to be stored so that the cog can access the bot at all times

    # you can have other parameters and fields here
    def __init__(self, bot):
        self.bot = bot

    ### BASIC COMMAND STUFF ###

    # command: ?greet
    @commands.command() # <- this line is to mark this function as a command. this NEEDS parentheses. if you're missing parens or have this line missing, the command will not show up
    async def greet(self, ctx): # <-- this line represents command name and arguments. all commands should be async and have a ctx
        """
        Says hi to you!
        """
        # ^ documentation for command

        # await ctx.send(message) to send a message to the channel the command was sent in
        # ctx.author to get author data

        # you HAVE to use await. if you do not use await on coroutines, 
        # nothing will happen and you probably will be very confused
        # so don't forget the await!
        await ctx.send("Hello " + ctx.author.name + "!")

    # command: ?farewell
    @commands.command()
    async def farewell(self, ctx):
        """
        Says bye to you!
        """
        await ctx.send("Bye " + ctx.author.name + "!")



    # notice: this method does NOT have a @commands.command(). It's just a regular helper command!
    def funfact(self):
        return random.choice([
            "14 people a year name their baby daughter Abcde (pronounced ab-sidy).",
            "Gay people are cool! :sunglasses:",
            "The Lego Ninjago TV Series has 14 seasons (as of June 12, 2021) and is still ongoing. <:panic:839223803573043240>", # CS Club panic emoji
            "14 \* 4 + 13 is a nice number.",
            "The iCarly 2021 remake is totally just for the money.",
            "Le-a is pronounced \"ledasha\"."
        ])

    # command: ?funfact, ?gimmeafact

    # the name field can be set to change the command's main name. by default, it's just the function name
    # all names in the aliases field are also accepted as command names
    @commands.command(name="funfact", aliases=["gimmeafact"])
    async def _funfact(self, ctx):
        """
        Give you a fun fact!
        """
        choice = self.funfact() # you can call functions from inside the class, like normal
        await ctx.send(choice)


    ### ARGUMENTS ###

    # command: ?copyme <arg>
    # try:
    #   ?copyme hello
    #   ?copyme hello hiya
    #   ?copyme "how are you?"
    @commands.command()
    async def copyme(self, ctx, arg): # <-- all args after ctx capture a single word
        """
        Tells you what argument you sent!
        """

        await ctx.send(ctx.author.name + " said `" + arg + "`! :open_mouth:")

    # command: ?copymynum <arg>
    # try:
    #   ?copymynum 14
    #   ?copymynum 1.1
    #   ?copymynum hi
    @commands.command()
    async def copymynum(self, ctx, arg: int): # <-- try to convert the first word into an int
        """
        Tells you what *number* you sent!
        """
        # arguments can be converted to many types including discord types (discord.User, discord.Message, etc.),
        # and some Python types (int, bool, float).
        # You can define your own converting types, too! See https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html#converters

        await ctx.send(ctx.author.name + " said `" + str(arg) + "`! Good number.")
    
    # command: ?copyme2 <arg> <arg> [args...]
    # try:
    #   ?copyme2 a b
    #   ?copyme2 a b c
    #   ?copyme2 a b c d e
    @commands.command()
    async def copyme2(self, ctx, arg1, arg2, *args): # *args = collect the rest of the arguments into a list
        """
        Example command. 
        
        Tells you what your first and second arguments were, 
        and gets lazy and just gives you a list of the rest of your arguments.
        """

        message =  f"Author: {ctx.author.name}\n"
        message += f"Arg 1: {arg1}\n"
        message += f"Arg 2: {arg2}\n"
        message += f"Rest: {args}\n"

        await ctx.send(message)
    
    # command: ?flipmsg <long string>
    # try:
    #   ?flipmsg hello
    #   ?flipmsg how are you?
    #   ?flipmsg racecar
    @commands.command()
    async def flipmsg(self, ctx, *, msg): # *, args = collect the rest of the message into a string
        """
        Reverses your message
        """
        revstr = "".join(reversed(msg))

        await ctx.send(ctx.author.mention + "\n" + revstr, allowed_mentions=discord.AllowedMentions.none())

    # command: ?addone [num]
    # try:
    #   ?addone
    #   ?addone 14
    @commands.command()
    async def addone(self, ctx, num: int = 0): # the = 0 allows you to have a default argument. If the user does not provide an argument, this is what the argument is assumed to be
        """
        Add one to an argument (because you clearly can't do math)
        """
        await ctx.send(f"{num} + 1 = {num + 1}")

    ### SUBCOMMANDS ###

    # If you want subcommands, instead of commands.command, you can use commands.group

    # if invoke_without_command is True, it will only call this command if you didn't call a subcommand
    # if False (default), it will always call this command first, even if you called a subcommand

    # command: ?random <start> <stop>
    @commands.group(invoke_without_command=True, aliases=["rand"])
    async def random(self, ctx, start: float, stop: float):
        """
        Get a random decimal number between the two values given
        """

        await ctx.send(str(random.uniform(start, stop)))
    
    # to make a subcommand, you use @<supercommand>.command(), as shown below
    # acts just like a regular command, but under ?random int rather than ?int

    # command: ?random int <start> <stop>
    @random.command(name="int")
    async def random_int(self, ctx, start: int, stop: int):
        """
        Get a random integer between the two values given (inclusive)
        """

        MIN_VALUE = -9007199254740991
        MAX_VALUE = 9007199254740992

        left, right = min(start, stop), max(start, stop)
        if left < MIN_VALUE:
            raise commands.BadArgument(f"Lower value is too small. It should be greater than {MIN_VALUE}.")
        elif right > MAX_VALUE:
            raise commands.BadArgument(f"Greater value is too big. It should be greater than {MAX_VALUE}.")

        await ctx.send(str(random.randint(left, right)))




# this function is OUTSIDE of the class
# this is important because d.py needs to know what to do when it reads this script

# this is the simplest cog setup, you may add more if something else needs to happen when this script is loaded
def setup(bot):
    # create an Example cog instance (with bot parameter), and add that instance to the list of bot cogs
    bot.add_cog(Example(bot))



# Need any more help?
# See https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html