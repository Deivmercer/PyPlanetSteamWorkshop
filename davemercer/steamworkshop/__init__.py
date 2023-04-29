from pyplanet.apps.config import AppConfig

from api import SteamWorkshopApi


class SteamWorkshop(AppConfig):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.api = SteamWorkshopApi()

	async def on_init(self):
		await self.api.create_session()

	async def on_start(self):
		await super().on_start()

	async def on_stop(self):
		await super().on_stop()

	async def on_destroy(self):
		await self.api.close_session()
