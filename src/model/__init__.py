from src.handler.add_new_command import creator
import peewee as pw

EMOJI_LIKE = chr(128077)
EMOJI_DISLIKE = chr(128078)

groups_database = pw.SqliteDatabase("groups.db")
commands_database = pw.SqliteDatabase("commands.db")

class Group(pw.Model):
    name = pw.TextField()
    username = pw.TextField(null = True)
    id = pw.IntegerField(primary_key = True)
    class Meta:
        database = groups_database

class Locks(pw.Model):
    group = pw.ForeignKeyField(Group, backref = "locks")
    forward = pw.BooleanField()
    class Meta:
        database = groups_database

# base class for normal and special commands
# contains the <Meta> class
class BaseCommandModel(pw.Model):
    class Meta:
        # everything about commands is saved in file <commands.db>
        database = commands_database

class NormalCommand(BaseCommandModel):
    names = pw.TextField()
    group = pw.ForeignKeyField(Group, backref="normal_commands")
    text = pw.TextField()
    delete_replied = pw.BooleanField()
    admin_only = pw.BooleanField()

class SpecialCommand(BaseCommandModel):
    type_id = pw.IntegerField()
    group = pw.ForeignKeyField(Group, backref="special_commands")
    regex = pw.TextField()
    data = pw.TextField(null=True)
    text = pw.TextField()
    delete_replied = pw.BooleanField()
    admin_only = pw.BooleanField()

groups_database.connect()
groups_database.create_tables([Group, Locks])

commands_database.connect()
commands_database.create_tables([NormalCommand, SpecialCommand])
