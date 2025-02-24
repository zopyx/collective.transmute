from collective.transmute import logger
from collective.transmute import settings
from dynaconf.loaders import toml_loader
from tempfile import NamedTemporaryFile

import typer


app = typer.Typer()


@app.command(name="settings")
def app_settings():
    """Report settings to be used by this application."""
    logger.info("Settings used by this application")
    logger.info("")
    data = {k.lower(): v for k, v in settings.pb_config.as_dict().items()}
    with NamedTemporaryFile(suffix=".toml", delete_on_close=False) as fp:
        filepath = fp.name
        toml_loader.write(filepath, data)
        response = fp.read().decode("utf-8")
    for line in response.split("\n"):
        logger.info(line)
