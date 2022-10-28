import jinja2
import sys
import os
from html import unescape

if getattr(sys, "is_standalone_binary", False):
    _templates_loader = jinja2.PackageLoader('bot.modules.messages.messages')
else:
    _TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')
    _templates_loader = jinja2.FileSystemLoader(_TEMPLATES_DIR)


_templates_env = jinja2.Environment(loader=_templates_loader, autoescape=jinja2.select_autoescape(['html']))

def _render_template(name: str, context: dict):
    template = _templates_env.get_template(name)
    return template.render(**context)

class BaseMessage:
    template = ''
    
    def __init__(self, template_context: dict = None, template: str = ''):
        if template_context is None:
            template_context = {}
        
        self._template_context = template_context
        self.template = template or self.template
        self._html = self._render_template()
    
    def _render_template(self):
        return _render_template(self.template, self._template_context)

    @property
    def html(self) -> str:
        return unescape(self._html)

    @property
    def escape_html(self) -> str:
        return self._html
