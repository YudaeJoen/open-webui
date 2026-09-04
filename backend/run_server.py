import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "open_webui.main:app",
        host="0.0.0.0",
        port=3000,
        log_level="info",
        access_log=True,
    )
