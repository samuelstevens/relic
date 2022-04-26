import logging

logger = logging.getLogger("relic-CLI")


def init(verbose: bool) -> None:
    log_format = "[%(levelname)s] %(message)s"

    if not verbose:
        logging.basicConfig(level=logging.INFO, format=log_format)
    else:
        logging.basicConfig(level=logging.DEBUG, format=log_format)


def debug(*args, **kwargs) -> None:  # type: ignore
    logger.debug(*args, **kwargs)


def info(*args, **kwargs) -> None:  # type: ignore
    logger.info(*args, **kwargs)


def warn(*args, **kwargs) -> None:  # type: ignore
    logger.warning(*args, **kwargs)


def error(*args, **kwargs) -> None:  # type: ignore
    logger.error(*args, **kwargs)
