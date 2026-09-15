"""A minimal fake standing in for the Anthropic SDK client in tests, so the
extraction pipeline can be tested without hitting the real API."""


class FakeTextBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class FakeMessageResponse:
    def __init__(self, text: str) -> None:
        self.content = [FakeTextBlock(text)]


class FakeMessages:
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []

    def create(self, **kwargs) -> FakeMessageResponse:
        self.calls.append(kwargs)
        text = self._responses.pop(0) if self._responses else "[]"
        return FakeMessageResponse(text)


class FakeAnthropicClient:
    def __init__(self, responses: list[str]) -> None:
        self.messages = FakeMessages(responses)
