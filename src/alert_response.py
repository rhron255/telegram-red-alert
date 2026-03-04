EMPTY_RESPONSE_TEXT = "\ufeff\r\n"


class AlertData:
    def __init__(
        self,
        alert_id: str,
        category: str,
        title: str,
        locations: list[str],
        description: str,
    ):
        self.id: str = alert_id
        self.category: str = category
        self.title: str = title
        self.locations: list[str] = locations
        self.description: str = description

    def __str__(self):
        return f"AlertResponse(id={self.id}, category={self.category}, title={self.title[::-1]}, data={list(map(lambda x: x[::-1], self.locations))}, desc={self.description[::-1]})"

    def __repr__(self):
        return self.__str__()
