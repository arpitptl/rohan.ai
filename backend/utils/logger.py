import logging
import colorlog
import sys
from datetime import datetime

def setup_logger(name='aa_gateway'):
    """Set up logger with color and timestamp formatting"""
    
    # Create logger
    logger = colorlog.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Create console handler
    console_handler = colorlog.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
     # Create formatter
    formatter = colorlog.ColoredFormatter(
        "%(asctime)s %(log_color)s%(levelname)-8s%(reset)s %(blue)s%(name)s%(reset)s %(purple)s%(filename)s:%(lineno)d%(reset)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    # Add formatter to console handler
    console_handler.setFormatter(formatter)
    
    # Add console handler to logger
    logger.addHandler(console_handler)
    
    return logger

# Create default logger instance
logger = setup_logger() 