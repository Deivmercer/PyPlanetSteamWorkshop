import logging
import os
from pyplanet.apps.config import AppConfig
from pyplanet.contrib.command import Command

from davemercer.steamworkshop.api import SteamWorkshopApi
from davemercer.steamworkshop.exceptions import SWInvalidResponse, SWMapNotFound

logger = logging.getLogger(__name__)


class SteamWorkshop(AppConfig):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.api = SteamWorkshopApi()

	async def on_init(self):
		await self.api.create_session()

	async def on_start(self):
		await self.instance.command_manager.register(
			Command(command="add", namespace="sw", target=self.add_sw_map, admin=True,
					description="Add map from Steam Workshop to the maplist.")
			.add_param('maps', nargs='*', type=str, required=True, help='Steam Workshop ID(s) of maps to add.'),
		)

	async def on_stop(self):
		await super().on_stop()

	async def on_destroy(self):
		await self.api.close_session()

	async def add_sw_map(self, player, data, **kwargs):
		sw_ids = data.maps

		if len(sw_ids) == 0:
			await self.instance.chat("Usage: sw add steam_workshop_id.", player)
			return

		# Prepare and fetch information about the maps from the Steam Workshop
		try:
			map_infos = await self.api.map_info(*sw_ids)
		except SWMapNotFound:
			await self.instance.chat("Error: map not found", player)
			return
		except SWInvalidResponse:
			await self.instance.chat("Error: invalid response from the Steam Workshop.", player)
			return

		try:
			if not await self.instance.storage.driver.exists(os.path.join("UserData", "Maps", "SteamWorkshop")):
				await self.instance.storage.driver.mkdir(os.path.join("UserData", "Maps", "SteamWorkshop"))
		except Exception:
			message = "Error: Can\'t check or create folder"
			await self.instance.chat(message, player.login)
			return

		# Fetch setting if juke after adding is enabled.
		juke_after_adding = await self.instance.setting_manager.get_setting(
			'admin', 'juke_after_adding', prefetch_values=True)
		juke_maps = await juke_after_adding.get_value()
		if 'jukebox' not in self.instance.apps.apps:
			juke_maps = False
		added_map_uids = list()

		for map_info in map_infos:
			try:
				# Test if map isn't yet in our current map list.
				if self.instance.map_manager.playlist_has_map(map_info[0]):
					raise Exception('Map already in playlist! Update? remove it first!')

				# Download and save file
				resp = await self.api.download(map_info[2])
				map_filename = os.path.join("SteamWorkshop", '{}-{}.Map.Gbx'.format(
					self.instance.game.game.upper(), map_info[0]
				))
				async with self.instance.storage.open_map(map_filename, 'wb+') as map_file:
					await map_file.write(await resp.read())
					await map_file.close()

				# Insert map to server.
				result = await self.instance.map_manager.add_map(map_filename, save_matchsettings=False)

				if result:
					added_map_uids.append(map_info[0])

					message = "Admin {} has added{} the map {}.".format(
						player.nickname, ' and juked' if juke_maps else '', map_info[1]
					)
					await self.instance.chat(message)
				else:
					raise Exception("Unknown error while adding the map")
			except Exception as e:
				logger.warning("Error when player {} was adding map {}".format(player.login, map_info[0]))
				message = "Error: Can\'t add map {}, Error: {}".format(map_info[1], str(e))
				await self.instance.chat(message, player.login)
