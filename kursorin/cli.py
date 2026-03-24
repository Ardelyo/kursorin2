"""KURSORIN CLI entry point."""
import click
from loguru import logger

@click.group()
def cli():
    """KURSORIN command line interface."""
    pass

@cli.command()
@click.option("--config", default=None, help="Path to config file")
def start(config):
    """Start KURSORIN in headless/CLI mode."""
    logger.info("CLI mode — starting KURSORIN")
    from kursorin.app import main
    main()

def main():
    cli()

if __name__ == "__main__":
    main()
