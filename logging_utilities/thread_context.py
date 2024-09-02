from threading import local


class ThreadContext(local):
    pass


thread_context = ThreadContext()
