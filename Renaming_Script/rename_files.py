#!/usr/bin/env python3
"""Interactively rename files in a folder, one at a time.

Opens each file in the folder (top level only, subfolders are ignored) with
the OS default application, then prompts in the terminal for a new name.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


def open_with_default_app(path: Path) -> None:
    if sys.platform.startswith("darwin"):
        subprocess.Popen(["open", str(path)])
    elif sys.platform.startswith("win"):
        import os

        os.startfile(path)  # type: ignore[attr-defined]
    else:
        subprocess.Popen(
            ["xdg-open", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def list_window_ids(name: str) -> list[str]:
    try:
        result = subprocess.run(
            ["wmctrl", "-l"], capture_output=True, text=True, timeout=2
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []

    ids = []
    for line in result.stdout.splitlines():
        parts = line.split(None, 3)
        if len(parts) < 4:
            continue
        win_id, title = parts[0], parts[3]
        if name.lower() in title.lower():
            ids.append(win_id)
    return ids


def close_windows_matching(name: str, timeout: float = 2.0) -> None:
    """Best-effort close of any window whose title contains `name` (via wmctrl).

    Waits (up to `timeout` seconds) for the window(s) to actually disappear
    before returning. Some default apps are single-instance / D-Bus activated,
    and asking them to open the next file while they're still mid-shutdown
    from the close request can cause that "open" to be silently dropped.
    """
    ids_to_close = list_window_ids(name)
    if not ids_to_close:
        return

    for win_id in ids_to_close:
        subprocess.run(
            ["wmctrl", "-ic", win_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    deadline = time.time() + timeout
    while time.time() < deadline:
        if not list_window_ids(name):
            break
        time.sleep(0.1)


def find_by_inode(folder: Path, ino: int) -> Path | None:
    """Find the file in `folder` that currently has inode `ino`.

    A file's inode survives a rename, so this lets us re-locate a file even
    if a conflict resolution (see unique_target) renamed it out from under us
    before its turn came up in the loop.
    """
    for candidate in folder.iterdir():
        if not candidate.is_file():
            continue
        try:
            if candidate.stat().st_ino == ino:
                return candidate
        except FileNotFoundError:
            continue
    return None


def unique_target(folder: Path, base: str, ext: str) -> Path:
    """Resolve base+ext against existing files in folder.

    If base+ext is free, use it as-is. If it's taken, the existing file is
    renamed to base+"1"+ext (if that slot is free), and the new name becomes
    the first free base+N+ext.
    """
    target = folder / f"{base}{ext}"
    if not target.exists():
        return target

    numbered_one = folder / f"{base}1{ext}"
    if not numbered_one.exists():
        target.rename(numbered_one)

    n = 1
    while (folder / f"{base}{n}{ext}").exists():
        n += 1
    return folder / f"{base}{n}{ext}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", nargs="?", help="Folder containing files to rename")
    args = parser.parse_args()

    folder_str = args.folder or input("Folder to rename files in: ").strip()
    folder = Path(folder_str).expanduser().resolve()

    if not folder.is_dir():
        print(f"Not a directory: {folder}")
        sys.exit(1)

    files = sorted(p for p in folder.iterdir() if p.is_file())
    if not files:
        print("No files found in that folder.")
        return

    # Snapshot each file's identity (inode) up front, so the processing order
    # is fixed even though a conflict resolution (see unique_target) might
    # rename a not-yet-processed file out from under it later in the run.
    work_items = [p.stat().st_ino for p in files]

    print(f"Found {len(files)} file(s) in {folder}. Ctrl+C at any time to stop.\n")

    for ino in work_items:
        path = find_by_inode(folder, ino)
        if path is None:
            # File was removed (or already handled) since the snapshot.
            continue

        print(f"Opening: {path.name}")
        open_with_default_app(path)

        try:
            new_base = input(
                f"  New name for '{path.name}' (blank = skip): "
            ).strip()
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)

        close_windows_matching(path.name)

        if not new_base:
            print("  Skipped.\n")
            continue

        new_base = new_base.replace(" ", "_")

        target = unique_target(folder, new_base, path.suffix)
        path.rename(target)
        print(f"  Renamed to: {target.name}\n")

    print("Done.")


if __name__ == "__main__":
    main()
