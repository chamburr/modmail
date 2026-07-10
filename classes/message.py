from __future__ import annotations

import copy
import logging

from typing import TYPE_CHECKING, Any

from discord import Role, User, message, utils
from discord.enums import MessageType, try_enum
from discord.flags import MessageFlags
from discord.http import Route, handle_message_parameters
from discord.message import Attachment, MessageReference, flatten_handlers
from discord.reaction import Reaction

from classes.embed import Embed
from classes.member import Member

if TYPE_CHECKING:
    from classes.channel import DMChannel, TextChannel
    from classes.state import State

log = logging.getLogger(__name__)


def interaction_body(content: Any = None, **kwargs: Any) -> dict[str, Any]:
    body: dict[str, Any] = {}

    embed = kwargs.get("embed")
    if embed is None and isinstance(content, Embed):
        embed = content
        content = None

    if embed is not None:
        body["embeds"] = [embed.to_dict()]

    if content is not None:
        body["content"] = str(content)

    return body


@flatten_handlers
class Message(message.Message):
    def __init__(self, *, state: State, channel: TextChannel | DMChannel, data: dict[str, Any]):
        self._state = state
        self._data = data
        self.id = int(data["id"])
        self.webhook_id = utils._get_as_snowflake(data, "webhook_id")
        self.attachments = [Attachment(data=x, state=self._state) for x in data["attachments"]]
        self.embeds = [Embed.from_dict(x) for x in data["embeds"]]
        self.application = data.get("application")
        self.activity = data.get("activity")
        self.channel = channel
        self.guild = getattr(channel, "guild", None)
        self._edited_timestamp = utils.parse_time(data["edited_timestamp"])
        self.type = try_enum(MessageType, data["type"])
        self.pinned = data["pinned"]
        self.flags = MessageFlags._from_value(data.get("flags", 0))
        self.mention_everyone = data["mention_everyone"]
        self.tts = data["tts"]
        self.content = data["content"]
        self.nonce = data.get("nonce")
        self._interaction = data.get("_interaction")

        ref = copy.copy(data.get("message_reference"))
        self.reference = MessageReference.with_state(state, ref) if ref is not None else None

        try:
            self._author = self._state.store_user(self._data["author"])
        except KeyError:
            self._author = None

        try:
            self._member = Member._from_message(message=self, data=self._data["member"])
        except KeyError:
            self._member = None

        for handler in ("call", "flags"):
            try:
                getattr(self, f"_handle_{handler}")(data[handler])
            except KeyError:
                continue

    @property
    def author(self) -> User | Member | None:
        return self._author

    @author.setter
    def author(
        self, value: User | Member | None
    ) -> None:
        self._author = value

    @property
    def member(self) -> Member | None:
        return self._member

    @member.setter
    def member(self, value: Any) -> None:
        return

    async def reactions(
        self,
    ) -> list[Reaction]:
        reactions = []

        for reaction in self._data.get("reactions", []):
            emoji = await self._state.get_reaction_emoji(reaction["emoji"])
            reactions.append(Reaction(message=self, data=reaction, emoji=emoji))

        return reactions

    async def mentions(
        self,
    ) -> list[User | Member]:
        try:
            mentions = self._data["mentions"]
            members: list[User | Member] = []
            guild = self.guild
            state = self._state

            if guild is not None:
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

    async def role_mentions(
        self,
    ) -> list[Role]:
        try:
            mentions = self._data["mention_roles"]
            roles = []

            if self.guild is not None:
                for role_id in map(int, mentions):
                    role = await self.guild.get_role(role_id)

                    if role is not None:
                        roles.append(role)

            return roles
        except KeyError:
            return []

    async def edit(self, content: Any = None, **kwargs: Any) -> Message:
        interaction = getattr(self, "_interaction", None)
        if interaction is not None:
            data = await self._state.http.request(
                Route(
                    "PATCH",
                    "/webhooks/{application_id}/{interaction_token}/messages/{message_id}",
                    application_id=interaction["application_id"],
                    interaction_token=interaction["token"],
                    message_id=self.id,
                ),
                json=interaction_body(content, **kwargs),
            )
            message = self._state.create_message(channel=self.channel, data=data)
            message._interaction = interaction
            return message

        if isinstance(content, Embed):
            kwargs["embed"] = content
        elif content is not None:
            kwargs["content"] = content

        params = handle_message_parameters(**kwargs)
        data = await self._state.http.edit_message(self.channel.id, self.id, params=params)
        return self._state.create_message(channel=self.channel, data=data)
