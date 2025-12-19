import logging

from utils.pluralize import pluralize


def display_config_file_data(len_processes: int, len_stock: int, len_to_optimize: int) -> None:
    logger = logging.getLogger(__name__)
    logger.info("%d %s, %d %s, %d %s to optimize",
        len_processes,
        pluralize(word="process", plural_end="es", amount=len_processes),
        len_stock,
        pluralize(word="stock", plural_end="s", amount=len_stock),
        len_to_optimize,
        pluralize(word="resource", plural_end="s", amount=len_to_optimize),
    )
