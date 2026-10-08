from typing import override

from chatddx.inventory import Source


class MemorySource(Source):
    vignettes: dict[str, bytes]

    @override
    def ids(self) -> list[str]:
        return sorted(self.vignettes)

    @override
    def fetch(self, id: str) -> bytes:
        try:
            return self.vignettes[id]
        except KeyError:
            raise self._missing(id) from None
