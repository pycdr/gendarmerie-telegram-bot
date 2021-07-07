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

3. edit `config.json` file (just set the token for now):

   ```bash
   {
   	"token": "<put your bot token here>",
   	"users":{
   		"admins": []
   	}
   }
   ```

4. put your texts for each commands in `texts.json` file:

   ```json
   {
   	"private": {
   		"command":{
   			"start": "for /start command in private",
   			...
   		}
   	},
   	"group": {
   		"command":{
   			"start": "for /start command in group for everyone",
   			...
   			"learning": {
   				"admin": "for !l/!learn/!learning command in group for admins",
   				"user": "for !l/!learn/!learning command in group for members"
   			},
   			...
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



