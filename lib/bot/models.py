from enum import Enum
from typing import Any, Union
from pydantic import BaseModel, Extra, Field


class User(BaseModel, extra=Extra.ignore):
    id: int
    is_bot: bool
    first_name: str = ''
    last_name: str | None
    username: str | None
    language_code: str | None
    is_premium: bool | None
    added_to_attachment_menu: bool | None
    can_join_groups: bool | None
    can_read_all_group_messages: bool | None
    supports_inline_queries: bool | None


class EChatType(str, Enum):
    private = 'private'
    group = 'group'
    supergroup = 'supergroup'
    channel = 'channel'


class Chat(BaseModel, extra=Extra.ignore):
    id: int
    type: EChatType
    title: str | None
    username: str | None
    first_name: str | None
    last_name: str | None
    description: str | None
    invite_link: str | None
    pinned_message: Union['Message', None]
  
  
class EEntityType(str, Enum):
    mention = 'mentrion'
    hashtag = 'hashtag'
    cashtag = 'cachtag'
    bot_command = 'bot_command'
    url = 'url'
    email = 'email'
    phone_number = 'phone_number'
    bold = 'bold'
    italic = 'italic'
    underline = 'underline'
    strikethrough = 'strikethrough'
    spoiler = 'spoiler'
    code = 'code'
    pre = 'pre'
    text_link = 'text_link'
    text_mention = 'text_mention'
    custom_emoji = 'custom_emoji'
    

class MessageEntity(BaseModel):
    type: EEntityType
    offset: int
    length: int
    url: str | None = None
    user: User | None = None
    language: str | None = None
    custom_emoji_id: str | None = None
    

class Message(BaseModel, extra=Extra.ignore):
    message_id: int
    from_: User | None = Field(title='from', alias='from', default=None)
    sender_chat: Chat | None = None
    date: int
    chat: Chat
    forward_from: User | None = None
    forward_from_chat: Chat | None = None
    forward_from_message_id: int | None = None
    forward_date: int | None = None
    reply_to_message: Union['Message', None] = None
    edit_date: int | None = None
    text: str | None = None
    entities: list[MessageEntity] | None = Field(default_factory=list)


class Update(BaseModel, extra=Extra.ignore):
    update_id: int
    message: Message | None
    edited_message: Message | None
    channel_post: Message | None
    edited_channel_post: Message | None
