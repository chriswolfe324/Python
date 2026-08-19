# How to Use

`rename_files.py` walks through the files in a folder one at a time, opens
each one so you can see what it is, and lets you type a new name for it in
the terminal.

## Requirements

- Python 3
- Linux: a default app associated with each file type (via `xdg-open`)
- Linux: `wmctrl` installed for auto-closing viewer windows (`sudo apt install wmctrl`)

## Running it

From this folder:

```
python3 rename_files.py /path/to/your/folder
```

Or run it with no argument and it will ask you for the folder path:

```
python3 rename_files.py
```

## What happens

1. The script looks at every **file** directly inside that folder. Files in
   subfolders are ignored, and subfolders themselves are never touched.
2. For each file, it opens it with your system's default application for
   that file type, then prompts in the terminal:

   ```
   New name for 'IMG_2931.jpg' (blank = skip):
   ```

3. Type a new name and press Enter:
   - You only need to type the **base name** — the original file extension
     (`.jpg`, `.pdf`, etc.) is kept automatically.
   - Any spaces you type are automatically converted to underscores.
   - Leaving it blank and pressing Enter **skips** that file and leaves it
     unchanged.
4. As soon as you press Enter, the script tries to close the viewer window
   (using `wmctrl`, matched by the file's name in the window title). This is
   best-effort — most common apps (image viewers, PDF readers, text editors)
   close cleanly, but it's not guaranteed for every app, since some don't put
   the filename in the window title or reuse an already-open window.
5. The script renames the file and moves on to the next one.
6. Repeat until every file has been handled, or you stop early.

## Stopping early

Press `Ctrl+C` at any prompt to cancel. Files already renamed stay renamed;
nothing further is touched.

## Name conflicts

If the name you type is already taken by another file in the folder, the
script resolves it automatically instead of asking you again:

- The **existing** file gets renumbered first, e.g. `photo.jpg` becomes
  `photo1.jpg`.
- Your **new** file then gets the next free number, e.g. `photo2.jpg`.
- If those numbers also happen to be taken, it keeps counting up
  (`photo3.jpg`, `photo4.jpg`, ...) until it finds a free name.

## Notes

- The script only renames files. It does not change ownership, permissions,
  or timestamps — those are untouched by a plain rename (the same as `mv`).
- It never modifies files in subfolders, and it never renames folders.
- The list of files to process, and their order, is fixed the moment the
  script starts. Each file is tracked by its underlying identity (inode), not
  its name, so if a conflict (see above) renames a file that hasn't been
  processed yet out from under it, the script still finds and prompts you for
  it under its new name — nothing gets silently skipped or revisited.
