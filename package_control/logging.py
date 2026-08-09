import logging

from . import text

CRITICAL = logging.CRITICAL
DEBUG = logging.DEBUG
ERROR = logging.ERROR
INFO = logging.INFO
WARNING = logging.WARNING


def getLogger(name):
    return logging.getLogger(name)


def set_loglevels(settings):
    for logger_name, log_level in settings.get("logging").items():
        logger = logging.getLogger(logger_name)
        try:
            logger.setLevel(log_level)
        except ValueError:
            logger.setLevel(WARNING)


class Formatter(logging.Formatter):
    """
    A formatter applying automatic text dedentation and stripping leading newlines

    This class turns python's logging machinary into a drop-in replacement for
    Package Control's `console_write` commands by applying identical text
    transformations, needed to support logging via triple-quoted block strings.
    """

    def format(self, record):
        """
        Format the specified record as text.

        Wraps `record.getMessage()` into `text.format()` to apply same text
        transformations as `console_write`.
        """
        # --- change start
        record.message = text.format(record.getMessage())
        # --- change end
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        s = self.formatMessage(record)
        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + record.exc_text
        if record.stack_info:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + self.formatStack(record.stack_info)
        return s


# Setup logger for package control
handler = logging.StreamHandler()
handler.setFormatter(Formatter(fmt="Package Control: %(message)s"))
logger = logging.getLogger("Package Control")
logger.addHandler(handler)
