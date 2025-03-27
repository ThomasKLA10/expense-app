import logging

def setup_logger(name):
    """Set up and return a logger with the given name"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Add console handler if not already present
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger 