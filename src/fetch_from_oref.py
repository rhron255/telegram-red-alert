import json
from typing import Any

import aiohttp

from alert_data import EMPTY_RESPONSE_TEXT


def create_session() -> aiohttp.ClientSession:
    """Create and configure a requests session."""
    session = aiohttp.ClientSession()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (compatible; Python requests)",
            "Referer": "https://www.oref.org.il/",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
        }
    )
    return session


async def fetch_data_from_oref(
    save_data: bool, file_to_fetch: str
) -> dict[str, Any] | list[dict[str, Any]] | None:
    try:
        async with create_session() as session:
            async with session.get(
                f"https://www.oref.org.il/WarningMessages/alert/{file_to_fetch}",
                timeout=10,
            ) as response:
                response.raise_for_status()

                text = (await response.text()).strip().replace("\0", "")
                if text == EMPTY_RESPONSE_TEXT or len(text) == 0:
                    return None
                if "{" not in text and "[" not in text:
                    return None
                if text[0] != "{" or text[0] != "[":
                    object_start = float("inf")
                    list_start = float("inf")
                    if "{" in text:
                        object_start = text.index("{")
                    if "[" in text:
                        list_start = text.index("[")
                    if list_start < object_start:
                        text = text[list_start:].encode("utf-8").decode("utf-8-sig")
                    else:
                        text = text[object_start:].encode("utf-8").decode("utf-8-sig")

                return json.loads(text)
    except Exception as e:
        e.add_note(
            await response.text()
            if "response" in locals()
            else "<no response from server>"
        )
        raise
