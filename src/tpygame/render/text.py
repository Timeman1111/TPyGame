class TextSurface:
    def __init__(self, x: int, y: int):
        self.x: int = x

        self.y: int = y

        self._content: str = ""

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, text: str):
        self._content = text

    def render(self):
        pass