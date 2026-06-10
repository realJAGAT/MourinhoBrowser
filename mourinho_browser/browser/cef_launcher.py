from cefpython3 import cefpython as cef


def initialize_cef():
    settings = {
        "multi_threaded_message_loop": False,
        "log_severity": cef.LOGSEVERITY_INFO,
        "ignore_certificate_errors": False,
    }
    cef.Initialize(settings)
    return cef


def shutdown_cef():
    cef.Shutdown()
