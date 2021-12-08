"""Logger facility module for the application."""
import logging
from logging.handlers import RotatingFileHandler  # TODO: why can't I use logging.handlers.RotatingFileHandler?
import sys
import settings


# TODO: use logging.basicConfig instead?
class Logger:
    def __init__(self, name):
        self.__name = name

        # Note that Loggers should NEVER be instantiated directly,
        # but always through the module-level function logging.getLogger(name).
        # Multiple calls to getLogger() with the same name will always return a reference to the same Logger object.
        self.__logger = logging.getLogger(name)

        self.__logger.setLevel(settings.DEFAULT_LOG_LEVEL)

        # Note: This variable won't get stored as an attribute (neither class attr nor instance attr)
        rotating_file_handler = RotatingFileHandler(
            settings.LOG_FILE_PATH,
            maxBytes=settings.LOG_FILE_MAX_SIZE,
            backupCount=settings.LOG_BACKUP_COUNT
        )

        rotating_file_handler.setFormatter(logging.Formatter(settings.LOGGING_FORMAT_STRING))

        self.__logger.addHandler(rotating_file_handler)

        # We will also write the log messages to stderr
        self.__logger.addHandler(logging.StreamHandler(stream=sys.stderr))  # TODO: is this the right way to do it?
        # self.__logger.addHandler(logging.StreamHandler(stream=sys.stdout))

    # TODO: seems like there is a better way (e.g. using decorators) to do this
    def debug(self, msg):
        self.__logger.debug(msg)

    def info(self, msg):
        self.__logger.info(msg)

    def critical(self, msg):
        self.__logger.critical(msg)

    def warning(self, msg):
        self.__logger.warning(msg)

    def exception(self, msg):
        self.__logger.exception(msg)
