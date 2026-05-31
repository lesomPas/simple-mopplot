# created by lesomras on 2025-5-31 
# (developing)


class TraitPath:
    def __init__(self, path: str):
        self.parts = self._parse(path)

    @staticmethod
    def _parse(path: str) -> list[str]:
        parts = []
        ptr = 0
        peek = lambda: path[ptr + 1] if ptr + 1 < len(path) else ""

        while True:
            start = ptr
            while ptr < len(path) and path[ptr] != ":":
                ptr += 1

            part = path[start:ptr].strip()
            if part == "":
                raise ValueError("empty part")
            parts.append(part)

            if ptr == len(path):
                return parts

            if peek() == ":":
                ptr += 2
            else:
                raise ValueError("unexpected char")
