from collections.abc import Iterable
import logging

logger = logging.getLogger(__name__)

class Command:
    def __init__(self, token):
        self.token = token

    def __repr__(self):
        return f"{self.__class__.__name__}"

    def prompts(self) -> Iterable[str]:
        raise NotImplementedError()

    def get_prompt(self) -> str:
        prompts = list(self.prompts())
        return prompts[0]

class SequenceCommand(Command):
    def __init__(self, tokens: list[Command]):
        self._tokens = tokens

    @property
    def tokens(self) -> list[Command]:
        return self._tokens

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.tokens})"

    def __len__(self) -> int:
        return len(self.tokens)

    def __getitem__(self, idx: int) -> Command:
        return self.tokens[idx]

    def __eq__(self, other):
        if isinstance(other, SequenceCommand):
            return self.tokens == other.tokens
        elif isinstance(other, list):
            return self.tokens == other
        else:
            return False

    def prompts(self) -> Iterable[str]:
        raise NotImplementedError()


class LiteralCommand(Command):
    def __init__(self, token: str):
        super().__init__(token)
        self.literal = token

    def __eq__(self, other):
        if isinstance(other, LiteralCommand):
            return self.literal == other.literal
        elif isinstance(other, str):
            return self.literal == other
        else:
            return False

    def __add__(self, other):
        if isinstance(other, LiteralCommand):
            return LiteralCommand(self.literal + " " + other.literal)
        raise TypeError("Cannot concatentate LiteralCommand with " + str(type(other)))

    def prompts(self) -> Iterable[str]:
        return [self.literal]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.literal!r})"

    def __str__(self) -> str:
        return self.literal

class VariantCommand(Command):
    def __init__(self, variants, min_bound=1, max_bound=1, sep=","):
        super().__init__(variants)

        min_bound, max_bound = min(min_bound, max_bound), max(min_bound, max_bound)
        self.min_bound = max(1, min_bound)
        self.max_bound = max_bound
        self.sep = sep
        self._weights = self._get_weights(variants)
        self._values = self._get_values(variants)

    def _get_weights(self, variants) -> list[float]:
        def get_weight(p) -> float:
            try:
                return p["weight"][0]
            except (TypeError, KeyError):
                return 1

        return [get_weight(p) for p in variants]

    def _get_values(self, variants) -> list[SequenceCommand]:
        def get_val(p) -> SequenceCommand:
            try:
                return p["val"]
            except (TypeError, KeyError) as e:
                logger.exception(e)
                return p

        return [get_val(p) for p in variants]

    def _combinations(self, k: int) -> Iterable[list[SequenceCommand]]:
        if k == 0:
            yield []
        else:
            for variant in self.variants:
                for item in self._combinations(k - 1):
                    # if variant not in item:
                    yield [variant] + item

    def __len__(self) -> int:
        return len(self._values)

    def __getitem__(self, index: int) -> SequenceCommand:
        return self._values[index]

    def __repr__(self) -> str:
        z = zip(self._weights, self._values)
        return f"{self.__class__.__name__}({list(z)!r})"

    def get_combinations(self, k: int) -> Iterable[list[SequenceCommand]]:
        return self._combinations(k)

    @property
    def variants(self) -> list[SequenceCommand]:
        return self._values

    @property
    def weights(self) -> list[float]:
        return self._weights


class WildcardCommand(Command):
    def __init__(self, wildcard_manager, token):
        super().__init__(token)
        self._wildcard_manager = wildcard_manager
        self._wildcard = token[0]

    @property
    def wildcard(self):
        return self._wildcard

    def __repr__(self):
        return f"{self.__class__.__name__}({self._wildcard!r})"


