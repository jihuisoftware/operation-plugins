"""Hermes tool for turning an approved manuscript into a timed storyboard."""
import json


def register(ctx):
    def generate(args, **kwargs):
        from .storyboard import generate_storyboard
        try:
            result = generate_storyboard(args, ctx.llm)
        except ValueError as exc:
            result = {'error': str(exc)}
        return json.dumps(result, ensure_ascii=False)

    ctx.register_tool(
        name='video_script_generate', toolset='video_script', handler=generate,
        schema={
            'name': 'video_script_generate',
            'description': '将用户提供的中文定稿改编为短视频。成功后向用户展示 markdown 分镜表。',
            'parameters': {
                'type': 'object',
                'properties': {
                    'body': {'type': 'string', 'minLength': 1, 'description': '完整定稿正文'},
                    'title': {'type': 'string', 'description': '原稿标题（可选）'},
                    'duration_seconds': {'type': 'integer', 'enum': [30, 60], 'default': 30},
                },
                'required': ['body'],
            },
        },
    )
