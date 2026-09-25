"""
Railway provider abstraction.

IMPORTANT:
IRCTC does not publish a general public booking API for arbitrary apps.
Use this adapter only with an API/web-service contract supplied to an
authorized IRCTC PSP/RSP or another authorized railway data provider.

Never use this adapter to bypass CAPTCHA/OTP, scrape IRCTC pages, or
automate an unauthorized personal account.
"""
import os
import requests


class RailwayProvider:
    def search_trains(self, source, destination, journey_date, quota="Tatkal"):
        raise NotImplementedError

    def get_pnr_status(self, pnr):
        raise NotImplementedError


class AuthorizedRailwayAPI(RailwayProvider):
    def __init__(self):
        self.base_url = os.getenv("RAILWAY_API_BASE_URL", "").rstrip("/")
        self.token = os.getenv("RAILWAY_API_TOKEN", "")
        self.timeout = int(os.getenv("RAILWAY_API_TIMEOUT", "15"))

    def _headers(self):
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _require_config(self):
        if not self.base_url:
            raise RuntimeError(
                "Authorized railway API is not configured. "
                "Set RAILWAY_API_BASE_URL and RAILWAY_API_TOKEN."
            )

    def search_trains(self, source, destination, journey_date, quota="Tatkal"):
        self._require_config()
        response = requests.get(
            f"{self.base_url}/trains",
            params={
                "from": source,
                "to": destination,
                "date": journey_date,
                "quota": quota,
            },
            headers=self._headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_pnr_status(self, pnr):
        self._require_config()
        response = requests.get(
            f"{self.base_url}/pnr/{pnr}",
            headers=self._headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()


class DemoRailwayProvider(RailwayProvider):
    def __init__(self, trains):
        self.trains = trains

    def search_trains(self, source, destination, journey_date, quota="Tatkal"):
        return {
            "source": source,
            "destination": destination,
            "journey_date": journey_date,
            "quota": quota,
            "provider": "demo",
            "trains": self.trains,
        }

    def get_pnr_status(self, pnr):
        return {
            "pnr": pnr,
            "provider": "demo",
            "status": "Demo status — connect an authorized PNR API",
        }


def get_provider(trains):
    mode = os.getenv("RAILWAY_PROVIDER", "demo").lower()
    if mode == "authorized":
        return AuthorizedRailwayAPI()
    return DemoRailwayProvider(trains)
