# gendarmerie-telegram-bot
gendarmerie (taken from the series "Barare Nights") can manage your telegram group, working with some JSON files. it's designed for special group handling.
### Abilities:
+ command:
  + project requests
  + irrelevant questions
  + non-directly question
  + questions about learning some programming languages
  + `/start`, `/help` and `/about` commands
# Usage

1. clone it from github:

   ```bash
   $ git clone https://github.com/pycdr/gendarmerie-telegram-bot
   $ cd gendarmerie-telegram-bot
   ```
   
2. install required libraries, listed in `requirements,txt`:

   ```bash
   $ pip install -r requirements.txt
   ```

3. edit `config.json` file (just set the token for now), else you'll give token and other things as argument to program:

   ```bash
   {
   	"token": "<put your bot token here>",
   	"users":{
   		"admins": []
   	}
   }
   ```

you can also do this (if `config.json`) doesn't exists:

```bash
$ ./main.py <token> -a @admin1 @admins2 ...
```

4. put your texts for each commands in `texts.json` file. this is its template data:

   ```json
	{
		"private": {
			"command":{
				"start": "<private/command/start>",
				"about": "<private/command/about>",
				"help": "<private/command/help>",
				"paste": "<private/command/paste>",
				"ask": "<private/command/ask>",
				"project": "<private/command/project>",
				"irrelevant": "<private/command/irrelevant>",
				"learning": "<private/command/learning>",
				"telegram_bot": "<private/command/telegram_bot>",
				"fun": {
					"1": "<private/command/fun/1>"
				}
			}
		},
		"group": {
			"command":{
				"start": "<group/command/start>",
				"about": "<group/command/about>",
				"help": "<group/command/help>",
				"paste": "<group/command/paste>",
				"ask": "<group/command/ask>",
				"project": {
					"admin": "<group/command/project/admin>",
					"user": "<group/command/project/user>"
				},
				"irrelevant": {
					"admin": "<group/command/irrelevant/admin>",
					"user": "<group/command/irrelevant/user>"
				},
				"learning": {
					"admin": "<group/command/learning/admin>",
					"user": "<group/command/learning/user>"
				},
				"telegram_bot": {
					"admin": "<group/command/telegram_bot/admin>",
					"user": "<group/command/telegram_bot/user>"
				},
				"fun": {
					"1": "<private/command/fun/1>"
				}
			}
		}
	}
   ```

5. then, run:

   ```bash
   $ chmod +x main.py
   $ ./main.py
   ```

# Contributing

if you want to help us develop, you can read `CONTRIBUTING.md` file to see how you can help us. also you may want to see `CHANGELOG.md` file to understand changes.



