"""
firebase_fastapi_wrapper
~~~~~~~~~~~~~~~~~~~~~~~~
A lightweight wrapper to run FastAPI apps inside Firebase Functions.

Basic usage::

    from firebase_fastapi_wrapper import FastAPIWrapper

    wrapper = FastAPIWrapper(app)
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__: str = version("firebase-fastapi-wrapper")
except PackageNotFoundError:  # running from source without installing
    __version__ = "0.0.0.dev0"

from firebase_fastapi_wrapper.wrapper import FastAPIWrapper

__all__ = ["FastAPIWrapper", "__version__"]
