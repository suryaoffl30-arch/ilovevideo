"""
Startup script that sets the correct event loop policy before starting uvicorn.
This is required for Python 3.13 on Windows to support subprocess operations.
"""
import sys
import asyncio

# MUST be set before importing any async libraries
if sys.platform == 'win32' and sys.version_info >= (3, 13):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("✓ Set WindowsProactorEventLoopPolicy for Python 3.13+")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
