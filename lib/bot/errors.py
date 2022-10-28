
class TelegramError(Exception):
    code = ''


class MessageNotModified(TelegramError):
    code = 'message is not modified'


class PhotoBadDimensions(TelegramError):
    code = 'PHOTO_INVALID_DIMENSIONS'


class ExportLinkPermissionDenied(TelegramError):
    code = 'not enough rights to export chat invite link'


class UserNotFound(TelegramError):
    code = 'user not found'


class ChatNotFound(TelegramError):
    code = 'chat not found'


class ChatWasUpgraded(TelegramError):
    code = 'group chat was upgraded to a supergroup chat'


class BotWasKicked(TelegramError):
    code = 'bot was kicked'


class BotWasBlocked(TelegramError):
    code = 'bot was blocked'