"""A minimal fake standing in for the OpenAI SDK client in tests, so the
extraction pipeline can be tested without hitting the real API."""


class FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeChoice:
    def __init__(self, content: str) -> None:
        self.message = FakeMessage(content)


class FakeChatCompletion:
    def __init__(self, content: str) -> None:
        self.choices = [FakeChoice(content)]


class FakeChatCompletions:
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []

    def create(self, **kwargs) -> FakeChatCompletion:
        self.calls.append(kwargs)
        content = self._responses.pop(0) if self._responses else '{"agreements": []}'
        return FakeChatCompletion(content)


class FakeChat:
    def __init__(self, responses: list[str]) -> None:
        self.completions = FakeChatCompletions(responses)


class FakeOpenAIClient:
    def __init__(self, responses: list[str]) -> None:
        self.chat = FakeChat(responses)

    @property
    def calls(self) -> list[dict]:
        return self.chat.completions.calls
