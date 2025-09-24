from rich.console import Console
from rich.theme import Theme

theme = Theme(
    {
        "info": "dim cyan",
        "warning": "dim yellow",
        "danger": "dim red",
        "success": "dim green",
        "partition": "b cyan",
        "nodes": "b yellow",
        "time": "b green",
        "qos": "b red",
        "allow": "b green",
        "deny": "b red",
    }
)
console = Console(theme=theme)
