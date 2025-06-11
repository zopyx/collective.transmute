"""
Command Line Interface for collective.transmute.

This module provides the main CLI application using Typer, with subcommands
for different operations like data transformation, reporting, settings management,
and sanity checks.
"""

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
    
    This is the main entry point for the collective.transmute CLI application.
    It provides various subcommands for data transformation, reporting,
    and configuration management.
    
    Args:
        ctx: Typer context object
    """
    pass


app.add_typer(app_transmute)
app.add_typer(app_report)
app.add_typer(app_settings)
app.add_typer(app_sanity)


def cli():
    """Entry point for the CLI application.
    
    This function is called when the package is run as a module or
    when the CLI is invoked directly.
    """
    app()


__all__ = ["cli"]
