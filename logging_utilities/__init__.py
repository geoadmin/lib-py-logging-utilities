VERSION = (1, 3, 0)
if isinstance(VERSION[-1], str):
    # Support for alpha version: 0.1.0-alpha1
    __version__ = "-".join([".".join(map(str, VERSION[:-1])), VERSION[-1]])  # pragma: no cover
else:
    __version__ = ".".join(map(str, VERSION))
