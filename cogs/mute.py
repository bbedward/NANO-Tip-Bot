from discord.ext import commands
from discord.ext.commands import Bot, Context
from models.command import CommandInfo

import config
from util.discord.channel import ChannelUtil
from util.discord.messages import Messages
from db.models.muted import Muted
from db.models.user import User

## Command documentation
MUTE_INFO = CommandInfo(
    triggers = ["mute"],
    overview = "Mute a user by ID",
    details = f"No longer receive tip notifications from a specific user. Example: `{config.Config.instance().command_prefix}mute 419483863115366410`"
)

class Mute(commands.Cog):
    """Commands for admins only"""
    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_before_invoke(self, ctx: Context):
        ctx.error = False
        # Only allow mute commands in private channels
        msg = ctx.message
        if not ChannelUtil.is_private(msg.channel):
            ctx.error = True
            await Messages.send_error_dm(msg.author, "You can only do this in DM")
            return
        # See if user exists in DB
        user = await User.get_user(msg.author)
        if user is None:
            ctx.error = True
            await Messages.send_error_dm(msg.author, f"You should create an account with me first, send me `{config.Config.instance().command_prefix}help` to get started.")
            return
        elif user.frozen:
            ctx.error = True
            await Messages.send_error_dm(msg.author, f"Your account is frozen. Contact an admin if you need further assistance.")
            return
        ctx.user = user

    @commands.command(aliases=MUTE_INFO.triggers)
    async def mute_cmd(self, ctx: Context):
        if ctx.error:
            return

        msg = ctx.message
        user = ctx.user

        to_mute = []
        for u in ctx.message.content.split():
            try:
                u_id = int(u.strip())
                discord_user = self.bot.get_user(u_id)
                if discord_user is not None:
                    to_mute.append(discord_user.id)
            except Exception:
                pass

        if len(to_mute) < 1:
            await Messages.send_usage_dm(msg.author, MUTE_INFO)
            return

        # Mute users
        muted_count = 0
        for u in to_mute:
            try:
                target_user = await User.get_user(u)
                if target_user is not None:
                    await Muted.mute_user(user, target_user)
                    muted_count += 1
            except Exception:
                pass

        if muted_count < 1:
            await Messages.send_error_dm(msg.author, "I was unable to mute any users you mentioned.")
            return

        await Messages.send_success_dm(msg.authro, f"Successfully muted {muted_count} user(s)")