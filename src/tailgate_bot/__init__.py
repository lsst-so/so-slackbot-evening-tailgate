"""Evening Tailgate Meeting Slack bot for Vera Rubin Observatory.

See ``DESIGN.md`` for the behavior spec and ``README.md`` for setup and
deployment. The process entry point is :func:`tailgate_bot.app.main`,
exposed as the ``tailgate-bot`` console script (and ``python -m
tailgate_bot``).
"""

from importlib.metadata import PackageNotFoundError, version as _version

__all__ = ["__version__"]

try:
    __version__ = _version("so-slackbot-evening-tailgate")
except PackageNotFoundError:
    # Package is not installed (e.g. running from a source tree with no
    # editable install). setuptools-scm owns the real value at build time.
    __version__ = "0.0.0"
