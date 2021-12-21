from .add_new_command import creator as create_add_new_command
from .add_new_group import creator as create_add_new_group
from .add_special_command import creator as create_add_special_command
from .handle_messages import creator as create_messages_handler
from .captcha_creator import creator as create_captcha_creator_handler
from .captcha_handler import creator as create_captcha_handler_handler
from .get_command import creator as create_get_command_handler
from .get_special import creator as create_get_special_handler
from .del_command import creator as create_del_command_handler
from .del_special import creator as create_del_special_handler
from .del_group import creator as create_del_group_handler
from .set_locks import creator as create_set_locks_handler
from .start_command import creator as create_start_command
from .backup import creator as create_backup
from .watch import creator as create_watch
from .export import creator as create_export
from .database import creator as create_database
from .add_filter import creator as create_add_filter_handler
from .get_filter import creator as create_get_filter_handler
from .del_filter import creator as create_del_filter_handler
from .get_score import creator as create_get_score_handler

CREATORES = (
    create_add_new_command,
    create_add_new_group,
    create_add_special_command,
    create_messages_handler,
    create_get_command_handler,
    create_get_special_handler,
    create_del_command_handler,
    create_del_special_handler,
    create_set_locks_handler,
    create_del_group_handler,
    create_captcha_creator_handler,
    create_start_command,
    create_backup,
    create_watch,
    create_export,
    create_database,
    create_get_score_handler,
    create_captcha_handler_handler,
    # create_add_filter_handler, ---> BUG: MessageHandler at state <GET_REGEX> is not detected by PTB
    # create_get_filter_handler,
    # create_del_filter_handler, 
)

def get_handlers(model, token):
    for creator in CREATORES:
        yield creator(model, token)
