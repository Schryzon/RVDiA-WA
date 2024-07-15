"""
Schryzon/Jayananda
RVDiA (Revolutionary Virtual Dialog Assistant)
Feel free to modify and do other stuff.
Contributions are welcome.
Licensed under the MIT LICENSE.
Made with Quart, an async version of Flask.

UNRAM accepted me, dawg!
"""

import logging
from app import create_app


app = create_app()

if __name__ == "__main__":
    logging.info("RVDiA, booted up. Initiating ASYNC mode.")
    #app.run(host="0.0.0.0", port=8000)
    app.run(host="0.0.0.0", port=8000, debug = True)