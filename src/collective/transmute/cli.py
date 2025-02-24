from collective.transmute.commands.report import app as app_report
from collective.transmute.commands.sanity import app as app_sanity
from collective.transmute.commands.settings import app as app_settings
from collective.transmute.commands.transmute import app as app_transmute

import typer


app = typer.Typer(no_args_is_help=True)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Welcome to transmute, the utility to transform data from
    collective.exportimport to plone.exportimport.
    """
    pass


app.add_typer(app_transmute)
app.add_typer(app_report)
app.add_typer(app_settings)
app.add_typer(app_sanity)


def cli():
    app()


__all__ = ["cli"]
