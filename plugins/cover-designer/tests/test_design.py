"""Local cover candidates are reproducible, bounded, and preserve publication authority."""
from io import BytesIO

from PIL import Image
import pytest

from cover_designer.cover_design import normalized, TEMPLATES
from cover_designer.cover_renderer import render
@pytest.mark.parametrize('template', list(TEMPLATES))
def test_layout_keeps_tool_names_and_chinese_phrases_intact_and_inside_canvas(template):
    from hermes_platform.fonts import chinese_font
    spec = normalized({'title': 'CodeGraph降本数据待核实', 'subtitle': '资料整理，结论待核实',
                       'keywords': ['预索引', '数据边界', '使用建议'], 'template': template}, '')
    raw, layout = render(spec, chinese_font())
    assert Image.open(BytesIO(raw)).size == (1080, 1440)
    lines = layout['title']['lines']
    assert 'CodeGraph' in lines and not any(line.endswith('数') for line in lines)
    assert ''.join(lines) == spec['title']
    x, y, width, height = layout['title']['box']
    assert x + width <= 1080 and y + height <= 1440
    assert layout['title']['used_height'] <= height
    assert layout['title']['font_size'] >= 36


def test_optional_model_cover_fields_are_compatible_but_user_input_is_bounded():
    spec = normalized({'title': None, 'template': {}, 'palette': [], 'keywords': '工具、方法'}, '合法标题')
    assert spec['title'] == '合法标题' and spec['template'] == 'editorial'
    assert spec['keywords'] == ['工具', '方法']
    with pytest.raises(ValueError):
        normalized({'title': '标题' * 30}, '文章标题', strict=True)


def test_keyword_phrases_do_not_split_tool_names_or_override_explicit_line_breaks():
    from PIL import ImageDraw
    from hermes_platform.fonts import chinese_font
    from cover_designer.cover_typography import tokens, fit
    assert 'Claude Code' in tokens('Claude Code 与 CodeGraph', ('Claude Code', 'Code'))
    assert 'CodeGraph' in tokens('Claude Code 与 CodeGraph', ('Claude Code', 'Code'))
    draw = ImageDraw.Draw(Image.new('RGB', (1080, 1440)))
    _, lines, _ = fit(draw, 'CodeGraph\n真的更省 Token？', chinese_font(), width=856, height=510, maximum=106)
    assert lines == ['CodeGraph', '真的更省 Token？']
