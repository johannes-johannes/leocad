# Web LDraw Viewer

This directory provides a minimal Three.js setup for exploring LeoCAD's bundled LDraw
part library inside a browser. The viewer is intentionally lightweight so it can run
inside a development container without additional tooling.

## Prerequisites

* Python 3.8 or newer (already bundled with the dev container)
* Network access so the browser can load Three.js modules from the unpkg CDN

## Usage

From the repository root run:

```bash
python webviewer/run.py
```

The script performs the following steps:

1. Extracts `resources/library.zip` into `webviewer/public/ldraw/` if the folder does
   not already exist.
2. Copies the supplied `LDConfig.ldr` colour table into that folder.
3. Generates `webviewer/public/parts_index.json`, a compact catalogue of the parts
   present in the bundled library.
4. Starts a simple HTTP server on `http://127.0.0.1:8000` that serves the static
   assets under `webviewer/public/`.

Open the reported URL in a browser. A dropdown lets you choose any part from the
embedded library, and the model renders via Three.js's `LDrawLoader`.

To rebuild the index or refresh the extracted library, delete the
`webviewer/public/ldraw/` folder and rerun the command.

## Project layout

```
webviewer/
  assets/
    LDConfig.ldr          # colour configuration copied into the public folder
  public/
    index.html            # entry point loading the viewer UI
    main.js               # browser-side logic that drives Three.js
    styles.css            # simple styling for the viewer UI
  run.py                  # helper that unpacks the library and runs a static server
```

You can customise the viewer by editing `public/main.js`. It currently renders
individual part files, but you can point it at any `.ldr`/`.mpd` file once the
library has been extracted.

