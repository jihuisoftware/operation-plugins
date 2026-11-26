from cover_designer.cover_cartoon_catalog import CHARACTERS, GROUPS
from cover_designer.cover_design import normalized
from cover_designer.cover_design import variations
from cover_designer.cover_renderer import render
from hermes_platform.fonts import chinese_font


def test_cartoon_candidates_keep_selected_character_and_palette(tmp_path, monkeypatch):
    monkeypatch.setenv('HERMES_HOME', str(tmp_path))
    spec = normalized({'template': 'cartoon', 'variant': 'bear-girl', 'title': '荷兰猪第一周',
                       'keywords': ['新手必看'], 'subtitle': '从布置小窝开始'}, '', strict=True)
    choices = variations(spec)
    assert choices[0] == spec
    for choice in choices:
        assert choice['variant'] in GROUPS['日系小人']
        _, layout = render(choice, chinese_font())
        assert ''.join(layout['title']['lines']) == spec['title']


def test_default_column_label_is_absent_and_the_same_words_can_be_a_title():
    for fields in ({}, {'eyebrow': '主题分享'}):
        spec = normalized({'template': 'cartoon', **fields}, '我的主题分享')
        assert spec['eyebrow'] == ''
        assert spec['title'] == '我的主题分享'
    assert normalized({'eyebrow': '饲养日记'}, '荷兰猪')['eyebrow'] == '饲养日记'
