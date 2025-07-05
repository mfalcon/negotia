from pathlib import Path
from jinja2 import Environment, FileSystemLoader, BaseLoader, DictLoader

class TemplateManager:
    def __init__(self, root: str = None):
        # Si no se indica root, usar <paquete>/prompts
        root = root or Path(__file__).resolve().parent.parent / "prompts"
        self.env = Environment(
            loader=FileSystemLoader(str(root)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )

    def render(self, template_path: str, **ctx) -> str:
        template = self.env.get_template(template_path)
        return template.render(**ctx)
    
    def render_custom(self, custom_prompt: str, **ctx) -> str:
        """Render a custom prompt string directly instead of loading from file."""
        template = self.env.from_string(custom_prompt)
        return template.render(**ctx) 