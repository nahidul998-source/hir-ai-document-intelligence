import os
import sys
import uvicorn

if __name__ == "__main__":
    os.environ["DATABASE_URL_OVERRIDE"] = "sqlite+aiosqlite:///./hir_dev.db"
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8002
    print(f"Starting uvicorn backend server on port {port}...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")
