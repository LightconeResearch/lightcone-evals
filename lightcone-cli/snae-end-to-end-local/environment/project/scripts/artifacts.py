"""Package multi-file scientific results as one reproducible Lightcone artifact."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


def write_archive(path: str | Path, members: dict[str, str]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w") as archive:
        for name, content in sorted(members.items()):
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, content.encode("utf-8"))
