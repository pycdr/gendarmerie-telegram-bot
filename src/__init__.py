def start_bot(
    token: str,
    base_url: str = None
):
    from .bot import Bot
    from . import model
    bot = Bot(
        token = token,
        base_url = base_url,
        model = model
    )
    bot.start()

def start_model_test(
    token: str,
    base_url: str = None
):
    print("not developed yet :(")
    exit()