from collective.transmute import logger
from collective.transmute.settings import pb_config
from collective.transmute.utils import check_steps

import typer


app = typer.Typer()


@app.command()
def sanity() -> None:
    """Run a sanity check on pipeline steps."""
    logger.info("Pipeline Steps")
    logger.info("")
    pipeline_status = True
    for name, status in check_steps(pb_config.pipeline.steps):
        pipeline_status = pipeline_status and status
        status_check = "✅" if status else "❗"
        logger.info(f" - {name}: {status_check}")
    status_check = "✅" if pipeline_status else "❗"
    logger.info(f"Pipeline status: {status_check}")
