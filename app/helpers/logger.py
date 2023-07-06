import logging

def get_logger(log_level):
    formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s | %(message)s')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logging.getLogger().handlers = []

    logger = logging.getLogger('my_logger')
    logger.setLevel(log_level)
    logger.addHandler(handler)
    
    return logger