# gendarmerie-telegram-bot

gendarmerie (taken from the series "Barare Nights") can manage your telegram group, working with python-telegram-bot and sqlite3. it's designed for special group handling.

## Usage

1. clone it from github:

   ```bash
   git clone https://github.com/pycdr/gendarmerie-telegram-bot
   cd gendarmerie-telegram-bot
   ```

2. install required libraries, listed in `requirements,txt`:

   ```bash
   pip install -r requirements.txt
   ```

3. set `TOKEN` (bot token - required), `ADMIN` (bot admin telegram id - required) and `WEBHOOK` (webhook URL) in `.env`

4. then, run:

   ```bash
   chmod +x main.py
   ./main.py
   ```
