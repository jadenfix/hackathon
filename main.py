"""Compatibility import and executable entry point for :mod:`hackathon.main`."""

from importlib import import_module
import sys

_executed_as_script = __name__ == "__main__"
_module = import_module('hackathon.main')
globals().update(_module.__dict__)
sys.modules[__name__] = _module

if _executed_as_script:
    _module.main()
