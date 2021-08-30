from .add_new_command import creator as create_add_new_command
from .add_new_group import creator as create_add_new_group
from .add_special_command import creator as create_add_special_command
from .handle_messages import creator as create_messages_handler
from .handle_status_messages import creator as create_status_messages_handler
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
    create_status_messages_handler,
    create_start_command,
    create_backup,
    create_watch,
    create_export,
    create_database
)

def get_handlers(model, token):
    for creator in CREATORES:
        yield creator(model, token)
