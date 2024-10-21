from backend.app.main import fast_api_app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(fast_api_app, host="0.0.0.0", port=8000)
