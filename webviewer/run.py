#!/usr/bin/env python3
"""Run a simple static server for the LDraw web viewer."""

from __future__ import annotations

import argparse
import http.server
import json
import os
import socketserver
import sys
from pathlib import Path
from zipfile import ZipFile

SUPPORTED_EXTENSIONS = {".dat", ".ldr", ".mpd"}

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = Path(__file__).resolve().parent / "public"
LDRAW_DIR = PUBLIC_DIR / "ldraw"
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
PARTS_INDEX = PUBLIC_DIR / "parts_index.json"
DEFAULT_PORT = 8000


def ensure_ldraw_library(force: bool = False) -> None:
    """Extract the bundled library into the public folder if needed."""
    if LDRAW_DIR.exists() and not force and not _library_has_parts():
        print("Existing LDraw folder is incomplete; rebuilding the library cache.")
        force = True

    if force and LDRAW_DIR.exists():
        _remove_ldraw_dir()

    if not LDRAW_DIR.exists():
        library_zip = REPO_ROOT / "resources" / "library.zip"
        if not library_zip.is_file():
            raise FileNotFoundError(f"Missing {library_zip}")

        with ZipFile(library_zip) as archive:
            archive.extractall(PUBLIC_DIR)

    colour_table = ASSETS_DIR / "LDConfig.ldr"
    if colour_table.is_file():
        target = LDRAW_DIR / "LDConfig.ldr"
        target.write_bytes(colour_table.read_bytes())

    if not _library_has_parts():
        raise FileNotFoundError(
            "The extracted library does not contain any part files. "
            "Try running with --rebuild to refresh the cache."
        )


def _remove_ldraw_dir() -> None:
    for path in sorted(LDRAW_DIR.rglob("*"), reverse=True):
        if path.is_file() or path.is_symlink():
            path.unlink()
        else:
            path.rmdir()
    LDRAW_DIR.rmdir()


def _library_has_parts() -> bool:
    parts_dir = LDRAW_DIR / "parts"
    if not parts_dir.is_dir():
        return False

    for path in parts_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            return True
    return False



def build_parts_index(
    limit: int | None = None,
    single_part: dict[str, str] | None = None,
) -> None:
    parts_dir = LDRAW_DIR / "parts"
    if not parts_dir.is_dir():
        raise FileNotFoundError("The parts directory was not found. Did the extraction succeed?")

    if single_part:
        entries = [single_part]
    else:
        entries = []
        for path in sorted(parts_dir.rglob("*")):
            if not path.is_file():
                continue

            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            # Preserve directory structure (e.g. patterned parts under "s/").
            part_id = str(path.relative_to(parts_dir)).replace(os.sep, "/")
            name = extract_part_name(path)
            entries.append({"id": part_id, "name": name})

            if limit and len(entries) >= limit:
                break

    PARTS_INDEX.write_text(json.dumps(entries, indent=2))

    if single_part:
        print(f"Indexed 1 part file ({single_part['id']})")
    else:
        print(f"Indexed {len(entries)} part files")


def resolve_part(part_id: str) -> dict[str, str]:
    part_id = part_id.strip()
    if not part_id:
        raise ValueError("Part identifier must be non-empty")

    parts_dir = LDRAW_DIR / "parts"
    if not parts_dir.is_dir():
        raise FileNotFoundError("The parts directory was not found. Did the extraction succeed?")

    candidate = parts_dir / part_id
    if candidate.is_file():
        rel_id = str(candidate.relative_to(parts_dir)).replace(os.sep, "/")
        return {"id": rel_id, "name": extract_part_name(candidate)}

    matches = [
        path
        for path in parts_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
        and path.name.lower() == part_id.lower()
    ]

    if not matches:
        raise FileNotFoundError(
            f"Could not find part '{part_id}'. Specify a relative path from the parts directory."
        )

    if len(matches) > 1:
        print(
            "Warning: multiple matches found for",
            part_id,
            "– using",
            matches[0].relative_to(parts_dir),
        )

    chosen = matches[0]
    rel_id = str(chosen.relative_to(parts_dir)).replace(os.sep, "/")
    return {"id": rel_id, "name": extract_part_name(chosen)}


def extract_part_name(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                line = line.strip()
                if not line or not line.startswith("0"):
                    continue
                if line.startswith("0 !") or line.startswith("0 BFC"):
                    continue
                if line.upper().startswith("0 FILE"):
                    continue
                if line.upper().startswith("0 NAME"):
                    # Format: 0 Name: description
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        return parts[1].strip() or path.stem
                return line[1:].strip() or path.stem
    except OSError:
        pass
    return path.stem


def serve(port: int) -> None:
    os.chdir(PUBLIC_DIR)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"Serving LDraw viewer on http://127.0.0.1:{port}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port for the HTTP server")
    parser.add_argument("--rebuild", action="store_true", help="Force regeneration of the library and index")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of parts listed in the dropdown")
    parser.add_argument(
        "--part",
        help=(
            "Show a single part in the viewer. Provide the file name or a relative path inside "
            "the parts directory (e.g. 3001.dat or s/3001p01.dat)."
        ),
    )
    args = parser.parse_args(argv)

    ensure_ldraw_library(force=args.rebuild)
    if args.part:
        entry = resolve_part(args.part)
        build_parts_index(single_part=entry)
    else:
        build_parts_index(limit=args.limit)
    serve(args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
