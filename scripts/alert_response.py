EMPTY_RESPONSE_TEXT = "\ufeff\r\n"


class AlertResponse:
    def __init__(self, data: dict):
        self.id = data["id"]
        self.category = data["cat"]
        self.title = data["title"]
        self.data = data["data"]
        self.desc = data["desc"]

    def __str__(self):
        return f"AlertResponse(id={self.id}, category={self.category}, title={self.title}, data={self.data}, desc={self.desc})"

    def __repr__(self):
        return self.__str__()
