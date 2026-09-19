import os
import sys
import argparse

# Ensure backend root is on PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run FREIGHT IQ Backend Service")
    parser.add_argument("--seed", action="store_true", help="Seed initial demo dataset")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto reload")
    args = parser.parse_args()

    if args.seed:
        from app.seed.seeder import seed_database
        seed_database()

    import uvicorn
    print(f"Starting FREIGHT IQ API Server on http://{args.host}:{args.port}")
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=not args.no_reload
    )
