
__author__ = 'alexisgallepe'

import run
import logging


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)

    run = run.Run()
    run.start()
