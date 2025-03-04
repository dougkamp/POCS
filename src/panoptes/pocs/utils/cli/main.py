import typer

from panoptes.pocs.utils.cli import config
from panoptes.pocs.utils.cli import sensor
from panoptes.pocs.utils.cli import image

app = typer.Typer()
state = {'verbose': False}

app.add_typer(config.app, name="config", help='Interact with the config server.')
app.add_typer(sensor.app, name="sensor", help='Interact with system sensors.')
app.add_typer(image.app, name="image", help='Interact with images.')


@app.callback()
def main(context: typer.Context,
         config_host: str = '127.0.0.1',
         config_port: int = 6563,
         verbose: bool = False):
    state.update({
        'config_host': config_host,
        'config_port': config_port,
        'verbose': verbose,
    })
    if verbose:
        typer.echo(f'Command options from main: {context.params!r}')


if __name__ == "__main__":
    app()
