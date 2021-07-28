from mysql.connector import connect
from mysql.connector.errors import IntegrityError

class MySQLHandler:
	def __init__(self, **kwargs):
		self.connection = connect(**kwargs)
		with self.connection.cursor() as cursor:
			cursor.execute("SHOW TABLES LIKE 'groups';")
			if len(list(cursor)) == 0: # 'groups' table doesn't exist
				cursor.execute(
					"CREATE TABLE groups (\
						group_id bigint NOT NULL, \
						group_name varchar(255) NOT NULL, \
						group_username varchar(255), \
						PRIMARY KEY (group_id)\
					);"
				)
			cursor.execute("SHOW TABLES LIKE 'commands';")
			if len(list(cursor)) == 0: # 'commands' table doesn't exist
				cursor.execute(
					"CREATE TABLE commands(\
					command varchar(255) NOT NULL,\
					text varchar(255),\
					delete_replied bool,\
					admin_only bool,\
					group_id bigint NOT NULL,\
					FOREIGN KEY (group_id) REFERENCES groups(group_id));"
				)

	def add_group(self, group_id: int, group_name: str, group_username: str = "NULL") -> (bool, str):
		if group_username != "NULL":
			group_username = repr(group_username)
		try:
			with self.connection.cursor() as cursor:
				cursor.execute(
					f"INSERT INTO groups \
					VALUES ({group_id}, {repr(group_name)}, {repr(group_username)});"
				)
				self.connection.commit()
		except IntegrityError as err:
			return False, repr(err)
		return True, ''

	def get_group(self, group_id: int):
		try:
			with self.connection.cursor() as cursor:
				cursor.execute(f"SELECT * FROM groups WHERE group_id = {group_id}")
				res = cursor.fetchall()[0]
		except IndexError:
			return False, None
		except Exception as err:
			return False, repr(err)
		return True, res

	def get_groups(self):
		try:
			with self.connection.cursor() as cursor:
				cursor.execute("SELECT * FROM groups")
				res = cursor.fetchall()
		except Exception as err:
			return False, repr(err)
		return True, res

	def get_commands(self, group_id):
		try:
			with self.connection.cursor() as cursor:
				cursor.execute("SELECT * FROM commands WHERE group_id="+str(group_id))
				res = cursor.fetchall()
		except Exception as err:
			return False, repr(err)
		return True, res
	
	
	def add_command(
		self, group_id: int, command: str, text: str,
		 delete_replied: bool = False, admin_only: bool = True
	) -> (bool, str):
		try:
			with self.connection.cursor() as cursor:
				cursor.execute(
					f"SELECT * FROM commands \
					WHERE group_id={group_id} AND command={repr(command)}"
				)
				if len(list(cursor)) != 0:
					return False, ''
				cursor.execute(
					f"INSERT INTO commands VALUES (\
						{repr(command)}, \
						{repr(text)}, \
						{int(delete_replied)}, \
						{int(admin_only)}, \
						{group_id}\
					);"
				)
				self.connection.commit()
		except IntegrityError as err:
			return False, repr(err)
		return True, ''

	def remove_command(self, group_id: int, command: str) -> (bool, str):
		try:
			with self.connection.cursor() as cursor:
				cursor.execute(
					f"DELETE FROM commands \
					WHERE command = {repr(command)} AND group_id = {group_id};"
				)
				self.connection.commit()
		except Exception as err:
			return False, repr(err)
		return True, ''

	def update_command(self, group_id: int, command: str, **updates) -> (bool, str):
		update_sql_code = ", ".join(
			f"{key} = '{value}'"
			for key, value in updates.items()
		)
		try:
			with self.connection.cursor() as cursor:
				cursor.execute(
					f"UPDATE commands\
					SET {update_sql_code}\
					WHERE group_id = {group_id} AND command = {repr(command)};"
				)
				self.connection.commit()
		except Exception as err:
			return False, repr(err)
		return True, ''

def test():
	def check(command):
		print(command.center(100, "-"))
		try:
			crs.execute(command)
			print(crs.fetchall())
		except Exception as err:
			print(repr(err))
	handler = MySQLHandler(
		**{x: input(x+": ")
		for x in ("host", "user", "password", "database")}
	)
	crs = handler.connection.cursor()
	check("DESCRIBE groups")
	check("SELECT * FROM groups")
	check("DESCRIBE commands")
	check("SELECT * FROM commands")
	handler.add_group(1234567890, "@example")
	check("SELECT * FROM groups")
	handler.add_command(1234567890, "!project", "این یک مثال است! so, ...", True, True)
	check("SELECT * FROM commands")
	print("> test again!")
	handler.add_group(1234567890, "@example")
	check("SELECT * FROM groups")
	handler.add_command(1234567890, "!project", "این یک مثال است! so, ...", True, True)
	check("SELECT * FROM commands")

if __name__ == "__main__":
	test()
