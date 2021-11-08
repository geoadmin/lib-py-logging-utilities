VERSION = (1, 2, 3)
if isinstance(VERSION[-1], str):
    # Support for alpha version: 0.1.0-alpha1
    __version__ = "-".join([".".join(map(str, VERSION[:-1])), VERSION[-1]])
else:
    __version__ = ".".join(map(str, VERSION))
