from pathlib import Path
from typeguard import typechecked

from layla_client.loaders import Loader


class LocalFileLoader(Loader):

    @typechecked
    def __init__(self, file_path: str | Path):
        if isinstance(file_path, str):
            self.file_path = Path(file_path)
        else:
            self.file_path = file_path

    def load(self) -> tuple[str, bytes]:
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        return (self.file_path.name, self.file_path.read_bytes())

