#!/usr/bin/env python3
# Delegate to the friendly smoke so we keep the nice ✅ logs.
import runpy, pathlib, sys
sys.exit(
    runpy.run_path(
        str(pathlib.Path(__file__).with_name("smoke_tools.py")),
        run_name="__main__"
    ) or 0
)
