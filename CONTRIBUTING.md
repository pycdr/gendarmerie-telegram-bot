here we have some files for each works. 2 `python` files and 2 `JSON` files:

## python files

### `main.py`

this file does the main file:

1. gets token and administrators IDs. it may get them from `config.json` (if exists), or from arguments with `argparse` library (if doesn't exists).
2. uses `watchdog` library to check if JSON files are edited, so it will update the `app.token`, `app.admins` or `app.texts`  methods if needed. bot won't be stopped.
3. defines `app` which contains an `bot.App` object to handle bot with it.
4. start the loop that executes `app.bot.polling()` and some other things.

### `bot.py`

this file has the main class for telegram bot:

* it uses `rich` library for CLI outputs. you can use its `rich.console.Console` object with `App.cli_console` method.
* it uses `telebot` library to handle your telegram bot. you can use its `telebot.Bot` object with `App.bot` attribute.
* `App.token` property is to set/get bot token, and `App.admins` property is to set/get bot administrators (if it's not in your group)
* `log_message` shows informations of the given message. each mode (in `App.handle`) uses it.
* `App.handle` method has 3 functions handling message (each has an special work) named `mode1` and `mode2` and `mode3`. its described in their doc string (e.g. use `help(App.handle.mode1)` to see for `mode1` method).
* `init` method defines commands:
  * `/start` for start command - mode 2
  * `/help` for help command - mode 2
  * `/about` for description - mode 2
  * `!l`, `!learn` and `!learning` for learning questions - mode 1
  * `!a` and `!ask` for non-directly questions - special mode!
  * `!p`, `!prj` and `!project` for project requests - mode 1
  * `!i` and `!irrelevant` for irrelevant questions - mode 1
  * `!b`, `!bot`, `!t` and `!telebot` for telegram bot questions - mode 1
* `run` method execute the bot and its required functions and the main loop (`App.bot.polling()`).
## JSON files

### `config.json`

this file contains bot informations:

* token of the bot
* list of administrators (except admins of your group)

### `texts.json`

this file contains all texts sending with commands. for example, when group creator sends `!prj` in group, the bot will send `bot.texts["group"]["command"]["project"]["admin"]` with method `bot.App.handle.mode1`.

* `private`
  * `command`
    * `start`: for `/start` command in private chat.
    * `about`: for `/about` command in private chat.
    * `help`: for `/help` command in private chat.
    * `ask`: for `!ask` command in private chat.
    * `paste`: for `!p` and `!paste` command in private chat.
    * `project`: for `!p`, `!prj` and `!project` command in private chat.
    * `irrelevant`: for `!i` and `!irrelevant` command in private chat.
    * `learning`: for `!l`, `!learn` and `!learning` command in private chat.
    * `telegram_bot`: for `!b`, `!bot` and `!telebot`  command in private chat.
    * `fun`: for `!fun` command in private chat - contains some other commands (defined as their code). e.g. `!fun1` in group will send `texts["private"]["command"]["fun"]["1"]`
* `group`
  * `command`
    * `start`: for `/start` command in group.
    * `about`: for `/about` command in group.
    * `help`: for `/help` command in group.
    * `ask`: for `!ask` command in group.
    * `paste`: for `!p` and `!paste` command in group.
    * `project`
      * `admin`: for `!p`, `!prj` and `!project` command in group (sent by admin)
      * `user`: for `!p`, `!prj` and `!project` command in group (sent by member)
    * `irrelevant`
      * `admin`: for `!i` and `!irrelevant` command in group (sent by admin)
      * `user`: for `!i` and `!irrelevant` command in group (sent by member)
    * `learning`
      * `admin`: for `!l`, `!learn` and `!learning` command in group (sent by admin)
      * `user`: for `!l`, `!learn` and `!learning` command in group (sent by member)
    * `telegram_bot`
      * `admin`: for `!b`, `!bot`, `!t` and `!telebot`  command in group (sent by admin)
      * `user`: for `!b`, `!bot`, `!t` and `!telebot`  command in group (sent by member)
    * `fun`: for `!fun` command in group (only for admins) - contains some other commands (defined as their code). e.g. `!fun1` in group will send `texts["group"]["command"]["fun"]["1"]`
