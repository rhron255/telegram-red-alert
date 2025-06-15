import json
import requests
import time

from alert_response import AlertResponse

EMPTY_RESPONSE_TEXT = "\ufeff\r\n"


def create_session() -> requests.Session:
    """Create and configure a requests session."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (compatible; Python requests)",
            "Referer": "https://www.oref.org.il/",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
        }
    )
    return session


def check_alerts(session: requests.Session) -> None:
    """Check for new alerts and notify subscribed users."""
    # First visit homepage to get cookies
    session.get("https://www.oref.org.il/", timeout=10)

    # Get alerts
    response = session.get(
        "https://www.oref.org.il/WarningMessages/alert/alerts.json", timeout=10
    )
    response.raise_for_status()
    # print(response.text)
    if response.text != EMPTY_RESPONSE_TEXT:
        try:
            print(AlertResponse(response.json()))
        except Exception as e:
            print(f"Error: {e}")
            print(response.text)
            print(
                AlertResponse(
                    json.loads(response.text.encode("utf-8").decode("utf-8-sig"))
                )
            )


if __name__ == "__main__":
    session = create_session()
    while True:
        check_alerts(session)
        time.sleep(1)
