import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Ensure the workspace is in the python path
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

from database.db import init_db
from services.ingestion import IngestionPipeline

def setup_logging(logs_dir: Path) -> None:
    """Configures logging to both file and standard output."""
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "pipeline.log"
    
    # Root logger configuration
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8")
        ]
    )

def main() -> None:
    load_dotenv()
    
    workspace_root = Path(__file__).resolve().parent
    logs_dir = workspace_root / "logs"
    setup_logging(logs_dir)
    
    logger = logging.getLogger("PipelineRunner")
    logger.info("Initializing Cricbuzz Cricket Data Ingestion Pipeline...")
    
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key or api_key == "your_rapidapi_key_here":
        logger.error(
            "RAPIDAPI_KEY is not set or contains placeholder value in .env. "
            "Please configure a valid RapidAPI Key in .env before running the pipeline."
        )
        sys.exit(1)
        
    try:
        # Initialize Database
        logger.info("Initializing PostgreSQL schema and tables...")
        init_db()
        logger.info("Database initialized successfully.")
        
        # Run Ingestion
        logger.info("Starting ingestion of recent matches...")
        pipeline = IngestionPipeline()
        results = pipeline.ingest_matches_list(match_type="recent")
        
        logger.info("=========================================")
        logger.info("INGESTION RUN SUMMARY")
        logger.info(f"Status: {results['status'].upper()}")
        logger.info(f"Matches Ingested: {results.get('matches_ingested', 0)}")
        logger.info(f"Scorecards Ingested: {results.get('scorecards_ingested', 0)}")
        logger.info(f"Errors Encountered: {results.get('errors', 0)}")
        logger.info("=========================================")
        
    except Exception as e:
        logger.critical(f"Pipeline crashed with unhandled exception: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
