"""Operations supplies an opaque, single-use local ticket for an authorized image."""
import json
import re

from plugins.plugin_storage import plugin_data_dir


def generate(args, **kwargs):
    from .render import compose
    ticket = args.get('ticket')
    if not isinstance(ticket, str) or not re.fullmatch(r'cover-[a-zA-Z0-9_-]{1,100}', ticket):
        raise ValueError('无效的封面任务')
    folder = plugin_data_dir('cover-designer') / 'exchange' / ticket
    spec = json.loads((folder / 'request.json').read_text(encoding='utf-8'))
    compose(folder, spec)
    return json.dumps({'ticket': ticket})


def register(ctx):
    ctx.register_tool(name='cover_generate', toolset='cover_designer',
                      schema={'name': 'cover_generate', 'description': '合成已授权任务的封面',
                              'parameters': {'type': 'object', 'properties': {'ticket': {'type': 'string'}},
                                             'required': ['ticket']}},
                      handler=generate)
