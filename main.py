import logging
from server import server

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    server.run(host='127.0.0.1', port=3000, debug=True)
