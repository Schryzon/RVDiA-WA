"""
Schryzon/Jayananda
RVDiA (Revolutionary Virtual Dialog Assistant)
Feel free to modify and do other stuff.
Contributions are welcome.
Licensed under the MIT LICENSE.

UNRAM, please accept me!!! >_<
"""

import logging

from app import create_app


app = create_app()

if __name__ == "__main__":
    logging.info("Flask app started")
    app.run(host="0.0.0.0", port=8000)