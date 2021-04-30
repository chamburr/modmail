import logging

from discord import message, utils
from discord.embeds import Embed
from discord.enums import MessageType, try_enum
from discord.flags import MessageFlags
from discord.message import Attachment, MessageReference, flatten_handlers
from discord.reaction import Reaction

from classes.guild import Guild
from classes.member import Member

log = logging.getLogger(__name__)


@flatten_handlers
class Message(message.Message):
    def __init__(self, *, state, channel, data):
        self._state = state
        self._data = data
        self.id = int(data["id"])
        self.webhook_id = utils._get_as_snowflake(data, "webhook_id")
        self.reactions = [
            Reaction(message=self, data=x, emoji="x") for x in data.get("reactions", [])
        ]
        self.attachments = [Attachment(data=x, state=self._state) for x in data["attachments"]]
        self.embeds = [Embed.from_dict(x) for x in data["embeds"]]
        self.application = data.get("application")
        self.activity = data.get("activity")
        self.channel = channel
        self._edited_timestamp = utils.parse_time(data["edited_timestamp"])
        self.type = try_enum(MessageType, data["type"])
        self.pinned = data["pinned"]
        self.flags = MessageFlags._from_value(data.get("flags", 0))
        self.mention_everyone = data["mention_everyone"]
        self.tts = data["tts"]
        self.content = data["content"]
        self.nonce = data.get("nonce")

        ref = data.get("message_reference")
        self.reference = MessageReference.with_state(state, ref) if ref is not None else None

        try:
            self._author = self._state.store_user(self._data["author"])
        except KeyError:
            self._author = None

        try:
            author = self._author
            try:
                author._update_from_message(self._data["member"])
            except AttributeError:
                author = Member._from_message(message=self, data=self._data["member"])
            self._member = author
        except KeyError:
            self._member = None

        for handler in ("call", "flags"):
            try:
                getattr(self, f"_handle_{handler}")(data[handler])
            except KeyError:
                continue

    @property
    def author(self):
        return self._author

    @author.setter
    def author(self, value):
        self._author = value

    @property
    def member(self):
        return self._member

    @member.setter
    def member(self, value):
        return

    async def mentions(self):
        try:
            mentions = self._data["mentions"]
            members = []
            guild = self.guild
            state = self._state

            if not isinstance(guild, Guild):
                members = [state.store_user(m) for m in mentions]
            else:
                for mention in filter(None, mentions):
                    id_search = int(mention["id"])
                    member = await guild.get_member(id_search)

                    if member is not None:
                        members.append(member)
                    else:
                        members.append(Member._try_upgrade(data=mention, guild=guild, state=state))

            return members
        except KeyError:
            return []

    async def role_mentions(self):
        try:
            mentions = self._data["mention_roles"]
            roles = []

            if isinstance(self.guild, Guild):
                for role_id in map(int, mentions):
                    role = await self.guild.get_role(role_id)

                    if role is not None:
                        roles.append(role)

            return roles
        except KeyError:
            return []
