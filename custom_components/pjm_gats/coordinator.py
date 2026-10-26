"""Coordinator for PJM GATS devices."""

from datetime import timedelta
import logging
import re
from typing import Any, override

from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


class PjmGatsApiError(Exception):
    """Exception for PJM GATS API errors."""


class PjmGatsAuthError(PjmGatsApiError):
    """Authentication error."""


class PjmGatsClient:
    """Async client for PJM GATS web portal."""

    BASE = "https://gats.pjm-eis.com"
    LOGIN_URL = f"{BASE}/gats2/login/index"
    LOGIN_POST = f"{BASE}/gats2/Login/Save"

    def __init__(self, session: ClientSession, username: str, password: str) -> None:
        """Initialize the client."""
        self.session = session
        self.username = username
        self.password = password

    async def login(self) -> None:
        """Authenticate with PJM GATS."""
        # GET login page → scrape CSRF token
        resp = await self.session.get(self.LOGIN_URL)
        resp.raise_for_status()
        text = await resp.text()

        soup = BeautifulSoup(text, "html.parser")
        token_input = soup.select_one('input[name="__RequestVerificationToken"]')
        if not token_input:
            raise PjmGatsApiError("CSRF token not found on login page")
        csrf = token_input["value"]

        # POST credentials
        payload = {
            "__RequestVerificationToken": csrf,
            "screenheight": "1080",
            "screenwidth": "1920",
            "loginName": self.username,
            "password": self.password,
        }
        headers = {"X-Request-Verification-Token": str(csrf)}
        resp = await self.session.post(
            self.LOGIN_POST,
            data=payload,
            headers=headers,
            allow_redirects=False,
        )

        if resp.status != 302:
            raise PjmGatsAuthError("Invalid credentials")

        # Follow redirect
        redirect_url = resp.headers["Location"]
        if not redirect_url.startswith("http"):
            redirect_url = self.BASE + redirect_url
        resp = await self.session.get(redirect_url, allow_redirects=True)
        resp.raise_for_status()

        # Verify session established
        if not any("ASP.NET_SessionId" in c.key for c in self.session.cookie_jar):
            raise PjmGatsAuthError("Session not established")

    async def _ensure_logged_in(self) -> None:
        """Ensure we have a valid session, login if needed."""
        if not await self._has_valid_session():
            await self.login()

    async def _has_valid_session(self) -> bool:
        """Check if current session is valid."""
        if not any("ASP.NET_SessionId" in c.key for c in self.session.cookie_jar):
            return False

        resp = await self.session.get(
            f"{self.BASE}/gats2/Home/Index",
            timeout=ClientTimeout(
                connect=15, sock_connect=15, sock_read=30, total=None
            ),
        )
        text = await resp.text()
        return resp.ok and "timed out" not in text.lower()

    async def get_home_page_data(self) -> dict[str, Any]:
        """Fetch and parse home page for sensor data."""
        await self._ensure_logged_in()

        resp = await self.session.get(f"{self.BASE}/gats2/Home/Index")
        resp.raise_for_status()
        text = await resp.text()

        soup = BeautifulSoup(text, "html.parser")
        data: dict[str, Any] = {}

        for table in soup.find_all("table"):
            text = table.get_text(" ", strip=True)

            # Main account summary table
            if "Generation" in text and "MWh" in text and "Account Summary" in text:
                self._parse_account_text(text, data)

            # Asset management table
            if "Asset Management" in text and "Unit ID" in text:
                self._parse_asset_text(text, data)

        return data

    def _parse_account_text(self, text: str, data: dict) -> None:
        """Extract all values from account summary table text."""
        # Generation MWh
        m = re.search(r"Generation\s+(\d+\.\d+)", text)
        if m:
            data["generation_mwh"] = float(m.group(1))

        # Certificate counts
        for label, key in (
            (r"Active\s+(\d+)(?!\.\d)", "certificates_active"),
            (r"CEPS\s+(\d+)", "certificates_ceps"),
            (r"On Bulletin Board\s+(\d+)", "certificates_on_bb"),
            (r"Reserved\s+(\d+)(?!\.\d)", "certificates_reserved"),
            (r"Certificate Total\s+(\d+)", "certificates_total"),
            (r"Active Hourly\s+([\d.]+)", "certificates_active_hourly"),
            (r"CEPS Hourly\s+([\d.]+)", "certificates_ceps_hourly"),
            (r"Reserved Hourly\s+([\d.]+)", "certificates_reserved_hourly"),
        ):
            m = re.search(label, text)
            if m:
                val = m.group(1)
                data[key] = float(val) if "." in val else int(val)

        # Inbox/Outbox
        for prefix, box_key in (("Inbox", "inbox"), ("Outbox", "outbox")):
            if prefix in text:
                for label, key in (
                    (rf"{prefix}Certificates(\d+)", f"{box_key}_certificates"),
                    (rf"{prefix}Generator Transfers(\d+)", f"{box_key}_transfers"),
                ):
                    m = re.search(label, text)
                    if m:
                        data[key] = int(m.group(1))
                if prefix == "Outbox":
                    m = re.search(r"OutboxStanding Orders(\d+)", text)
                    if m:
                        data["outbox_standing_orders"] = int(m.group(1))

    def _parse_asset_text(self, text: str, data: dict) -> None:
        """Extract generator info from asset management table text."""
        m = re.search(r"(NON\d+)\s+(.+?)\s+(ACT|INACT|PEND|RET)", text)
        if m:
            data["generator_id"] = m.group(1)
            data["generator_plant"] = m.group(2).strip()
            data["generator_status"] = m.group(3)


type PjmGatsConfigEntry = ConfigEntry[PjmGatsDataUpdateCoordinator]


class PjmGatsDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """Class to manage fetching PJM GATS data."""

    def __init__(self, hass: HomeAssistant, client: PjmGatsClient) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=30),
        )
        self.client = client

    @override
    async def _async_update_data(self) -> dict:
        """Fetch data from PJM GATS."""
        try:
            return await self.client.get_home_page_data()
        except PjmGatsAuthError as err:
            raise ConfigEntryAuthFailed from err
        except PjmGatsApiError as err:
            raise UpdateFailed(f"Error communicating with PJM GATS: {err}") from err
