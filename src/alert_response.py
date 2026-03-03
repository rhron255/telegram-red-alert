EMPTY_RESPONSE_TEXT = "\ufeff\r\n"


class AlertResponse:
    def __init__(self, data: dict):
        self.id = data["id"]
        self.category = data["cat"]
        self.title = data["title"]
        self.data = data["data"]
        self.desc = data["desc"]

    def __str__(self):
        return f"AlertResponse(id={self.id}, category={self.category}, title={self.title[::-1]}, data={list(map(lambda x: x[::-1], self.data))}, desc={self.desc[::-1]})"

    def __repr__(self):
        return self.__str__()
