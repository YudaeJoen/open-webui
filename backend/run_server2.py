import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import uvicorn

if __name__ == "__main__":
    config = uvicorn.Config(
        "open_webui.main:app",
        host="0.0.0.0",
        port=3000,
        log_level="info",
        access_log=True,
    )
    server = uvicorn.Server(config)
    server.run()
