import logging


def is_instance(attr, of_type):
    if isinstance(of_type, str):
        attr_class = type(attr)
        if '.' in of_type:
            return (
                '{}.{}'.format(attr_class.__module__, attr_class.__name__) == of_type or
                of_type in ['{}.{}'.format(c.__module__, c.__name__) for c in attr_class.__bases__]
            )
        return attr_class.__name__ == of_type or of_type in [
            c.__name__ for c in attr_class.__bases__
        ]
    return isinstance(attr, of_type)


class AttrTypeFilter(logging.Filter):
    """Filter attributes based on their types

    This filter can help in case multiple libraries/frameworks etc. use the
    same extra properties in the extra parameter of the logging. It filters
    these extra properties by type, either with a whitelist (the default) or
    with a blacklist.
    """

    def __init__(self, typecheck_list, *, is_blacklist=False):
        """Initialize the filter

        Args:
            typecheck_list: dict(key, type|list of types)
                A dictionary that maps keys to a type or a list of types.
                By default, it will only keep a parameter matching a key
                if the types match or if any of the types in the list match
                (white list). If in black list mode, it will only keep a
                parameter if the types don't match. Parameters not appearing
                in the dict will be ignored and passed though regardless of the
                mode (whitelist or blacklist).
            is_blacklist: bool (default: false)
                Whether the list passed should be a blacklist or a whitelist.
                To use both, simply include this filter two times, one time with
                this parameter set true and one time with this parameter set false.
        """
        self.typecheck_list = typecheck_list
        for key in self.typecheck_list:
            if not isinstance(self.typecheck_list[key], list):
                self.typecheck_list[key] = [self.typecheck_list[key]]
        self.is_blacklist = is_blacklist
        super().__init__()

    def filter(self, record):
        for key, whitelisted_types in self.typecheck_list.items():
            if not hasattr(record, key):
                continue
            item = getattr(record, key)
            if any(is_instance(item, t) for t in whitelisted_types) is self.is_blacklist:
                delattr(record, key)

        return True
