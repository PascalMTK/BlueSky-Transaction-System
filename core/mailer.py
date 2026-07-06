import threading


def send_async(target, *args, **kwargs):
    """Run a notification function (typically an email send) in a background
    thread so the HTTP response doesn't block on the SMTP round trip."""
    threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True).start()
