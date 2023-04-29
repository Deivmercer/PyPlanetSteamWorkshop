"""
Steam Workshop API client
"""
import aiohttp
from pyplanet import __version__ as pyplanet_version

from exceptions import SWInvalidResponse, SWMapNotFound


class SteamWorkshopApi:

    url = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    def __init__(self):
        self.session = None

    async def create_session(self):
        self.session = await aiohttp.ClientSession(
            headers={"User-Agent": "PyPlanet/{}".format(pyplanet_version)}
        ).__aenter__()

    async def close_session(self):
        await self.session.close()

    async def map_info(self, *sw_ids):
        if isinstance(sw_ids, str) or isinstance(sw_ids, int):
            sw_ids = [sw_ids]

        payload = dict()
        payload["itemcount"] = len(sw_ids)
        for i, sw_id in enumerate(sw_ids):
            payload["publishedfileids[{}]".format(i)] = sw_id

        res = await self.session.post(self.url, data=payload, headers=self.headers)

        if res.status == 404:
            raise SWMapNotFound("Map not found")
        elif res.status != 200:
            raise SWInvalidResponse("An error occurred")

        json = (await res.json())["response"]

        return [(map_info["filename"], map_info["file_url"]) for map_info in json["publishedfiledetails"]]
