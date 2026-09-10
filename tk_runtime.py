"""Support Python distributions that ship Tcl libraries as ZIP files."""
import os
import sys
import tempfile
import zipfile
from pathlib import Path


def prepare_tk():
    if getattr(sys, 'frozen', False):
        return
    root = Path(sys.base_prefix) / 'tcl'
    for stem, folder, variable in [('libtcl', 'tcl_library', 'TCL_LIBRARY'),
                                  ('libtk', 'tk_library', 'TK_LIBRARY')]:
        if os.environ.get(variable):
            continue
        archives = sorted(root.glob(stem + '*.zip'))
        if archives:
            archive = archives[-1]
            target = Path(tempfile.gettempdir()) / 'SkyTubeDownloader-Tk' / archive.stem
            if not (target / folder / ('init.tcl' if stem == 'libtcl' else 'tk.tcl')).exists():
                with zipfile.ZipFile(archive) as bundle:
                    bundle.extractall(target)
            os.environ[variable] = str(target / folder)
