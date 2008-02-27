import ecell.ui.model_editor.config as config

__all__ = (
    'CanvasWidgetWrapper',
    )

locals().update(
    __import__(
        '__' + config.canvas_peer, globals(), locals(), [ '*' ], -1
        ).__dict__
    )
