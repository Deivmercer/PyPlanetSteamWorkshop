class SteamWorkshopException(Exception):
	pass


class SWInvalidResponse(SteamWorkshopException):
	pass


class SWMapNotFound(SteamWorkshopException):
	pass
