from threading import local


class ThreadContext(local):
    """ThreadContext is a store for data that is thread specific.
    """


thread_context = ThreadContext()
