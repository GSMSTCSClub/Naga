import discord
from discord.ext import commands

import emoji
import inspect
import re
import string

### MATCHES ###
# match any custom emoji, "custom" is set to the ID of the matched emoji
CUSTOM_EMOJI_REGEX = r"(?:<a?:\w+?:(?P<custom>\d+)>)"
# match any custom emoji the user cannot access (e.g. :hello: not appearing), "pcustname" is set to the name of the matched emoji
PC_EMOJI_REGEX = r"(?::(?P<pcustname>\w+?):)"

# match any unicode emoji, "emoji" is set to the matched emote
# any \uFE0F is also captured to heed by discord's emote stuff
_all_unicode_emoji = emoji.get_emoji_regexp().pattern + r"|[\U0001F1E6-\U0001F1FF]"
UNI_EMOJI_REGEX = r"(?P<emoji>(?:{})\uFE0F*)".format(_all_unicode_emoji)

# capture everything else (under name "misc")
# if matched character is in EMO_MAP, use that emoji
LINE_MISC_REGEX = r"(?P<misc>10|.)"
MISC_REGEX = r"(?P<misc>.)" 

# match ranges
# examples: 1..5, 2-9, A-F, Q..Z
# "nrange" or "arange" matches full range
# "nL" or "aL" matches left bound (inclusive)
# "nR" or "aR" matches right bound (inclusive)
NUM_RANGE_REGEX = r"(?P<nrange>(?P<nL>10|\d)(?:-|\.\.)(?P<nR>10|\d))" # numeric range, 0..10 or 0-10
ALPHA_RANGE_REGEX = r"(?P<arange>(?P<aL>[A-Za-z])(?:-|\.\.)(?P<aR>[A-Za-z]))" # alphabetic range, a..z or a-z

_raw_emoji_regex = f"{CUSTOM_EMOJI_REGEX}|{PC_EMOJI_REGEX}|{UNI_EMOJI_REGEX}"

# all regexes that can be matched with the default ]poll <rxns> <msg> setting
EMOJI_REGEX = re.compile(f"{NUM_RANGE_REGEX}|{ALPHA_RANGE_REGEX}|{_raw_emoji_regex}|{MISC_REGEX}")
# all regexes that can be matched with the  ]poll lines <msg> setting
LINE_REGEX = re.compile(f"^(?:{UNI_EMOJI_REGEX})", re.M)
BLANK_TEXT = "** **"

EMO_MAP = {}
# add mapping from A-Z to their emoji counteparts
for n, c in enumerate(string.ascii_uppercase):
    EMO_MAP[c] = chr(127462+n)

for i in range(10):
    EMO_MAP[str(i)] = str(i) + u'\ufe0f\u20e3'

EMO_MAP.update({
    '10': '\U0001F51F',
     'y': '<:yes:826351259636072478>',
     'n': '<:no:826351260793307136>',
     'm': '<:maybe:826351274365550592>',
     '?': '\u2753',
     '!': '\u2757',
     '+': '\u2795'
})

EMOJI_CAP = 20

# aliases = "\n".join([
#     "",
#     "__Aliases__",
#     f"y: {EMO_MAP['y']}",
#     f"n: {EMO_MAP['n']}",
#     f"m: {EMO_MAP['m']}",
#     f"?: {EMO_MAP['?']}",
#     f"!: {EMO_MAP['!']}",
#     f"0-10: {EMO_MAP['0']}-{EMO_MAP['10']}",
#     f"A-Z: {EMO_MAP['A']}-{EMO_MAP['Z']}",
#     "",
#     "A..Z, 0..10 for a range of reactions",
# ])

# def add_aliases(doc):
#     doc = inspect.cleandoc(doc)
#     doc += "\n"
#     doc += aliases
#     return doc
def add_aliases(doc):
    return inspect.cleandoc(doc)

### ACTUAL POLLING STUFF ###

class Poll(commands.Cog):
    HELP_CATEGORY = 'Utils'
    AUTHORS = (141294044671246337,)

    def __init__(self, bot):
        self.bot = bot

    def parse_emoji_str(self, s, *, regex=EMOJI_REGEX, message=None, fallback_to_set=True):
        rxns = []
        guild = message and message.guild

        use_fallback = False
        for reaction in regex.finditer(s):
            try:
                lg = reaction.lastgroup
                m = reaction[lg]

                if lg == 'nrange':
                    l, r = map(int, [reaction['nL'], reaction['nR']])
                    
                    # if 0..10, add [0, 1, ..., 9, 10]
                    # if 10..0, add [10, 9, ..., 1, 0]
                    sign = 1 if l <= r else -1
                    rxns.extend(EMO_MAP[str(o)] for o in range(l, r + sign, sign))

                elif lg == 'arange':
                    l, r = map(lambda c: ord(c.upper()), [reaction['aL'], reaction['aR']])

                    # if A..Z, add [A, B, ..., Y, Z]
                    # if Z..A, add [Z, Y, ..., B, A]
                    sign = 1 if l <= r else -1
                    rxns.extend(EMO_MAP[chr(o)] for o in range(l, r + sign, sign))

                elif lg == 'custom':
                    # if we're here, then the user put a custom emoji 
                    eid = int(m)

                    # if bot knows emoji, use known emoji
                    # else, check the message for the emoji 
                    emoji = self.bot.get_emoji(eid) or \
                            next((r.emoji for r in message.reactions if r.custom_emoji and r.emoji.id == eid), None)
                    if emoji: 
                        rxns.append(emoji)
                    elif fallback_to_set: 
                        use_fallback = True
                        break

                elif lg == "pcustname" and guild is not None:
                    # if we're here then it is a non-nitro user failing to using an animated emoji / out-of-guild emoji

                    emoji = next(
                            (e for e in guild.emojis if e.name == m), # if emoji in guild
                            next((r.emoji for r in message.reactions if r.custom_emoji and r.emoji.name == m), # if emoji in message
                            None) # i dunno
                        )
                    if emoji:
                        rxns.append(emoji)
                    elif fallback_to_set: 
                        use_fallback = True
                        break

                elif lg == 'emoji':
                    rxns.append(m)

                elif lg == 'misc':
                    emoji = EMO_MAP.get(m, None)
                    if emoji: 
                        rxns.append(emoji)
                    elif fallback_to_set: 
                        use_fallback = True
                        break

            except: pass

        if use_fallback:
            return [EMO_MAP[c] for c in 'ynm']
            
        # remove duplicates (& preserve order)
        rxns = list(dict.fromkeys(rxns))
        return rxns

    @staticmethod
    async def send_rxns(rxns, msg: discord.Message = None, more_msgs=True):
        chan = msg.channel
        if not msg: msg = await chan.send(BLANK_TEXT) # shouldn't ever happen, but if it does!

        i = 0
        for rxn in rxns:
            if more_msgs and i == EMOJI_CAP:
                i %= EMOJI_CAP
                msg = await chan.send(BLANK_TEXT)
            try:
                await msg.add_reaction(rxn)
                i += 1
            except: pass
        
    @commands.group(invoke_without_command=True, aliases=["polls"],
        help=add_aliases("""\
        Create a poll.
        """)
    )
    async def poll(self, ctx, reactions, *, content=''):
        msg = ctx.message
        rxns = self.parse_emoji_str(reactions, message=msg)
        await self.send_rxns(rxns, msg)

    @poll.command(name="lines",
        help=add_aliases("""\
        Create a poll. The emotes on each line are used as the reactions.
        """)
    )
    async def poll_lines(self, ctx, *, content=""):
        msg = ctx.message
        msgstr = "\n".join(content.strip().splitlines())

        rxns = self.parse_emoji_str(msgstr, regex=LINE_REGEX, message=msg)
        await self.send_rxns(rxns, msg)

def setup(bot):
    bot.add_cog(Poll(bot))
