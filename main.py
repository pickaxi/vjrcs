from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, ADMINS

class Bot(Client):

    def __init__(self):
        super().__init__(
            "techvj login",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="TechVJ"),
            workers=50,
            sleep_threshold=10
        )

    async def start(self):
        await super().start()
        print('Bot Started')

        # Ensure ADMINS is always treated as a list
        admins = [ADMINS] if isinstance(ADMINS, int) else ADMINS

        for admin in admins:
            try:
                await self.send_message(admin, "Bot Restarted ✅")
            except Exception as e:
                print(f"Failed to send message to {admin}: {e}")

    async def stop(self, *args):
        await super().stop()
        print('Bot Stopped Bye')
