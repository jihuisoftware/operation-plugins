"""Exercise the registered tool without requiring a configured model."""
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('video_script', root / '__init__.py')
plugin = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = plugin
spec.loader.exec_module(plugin)


BODY = '编辑先核对标题，再检查正文。'


def shot(seconds=15, **fields):
    return {'seconds': seconds, 'visual': '录屏：指向标题', 'voiceover': '先核对标题。',
            'subtitle': '核对标题', 'source_quote': '先核对标题', **fields}


def reply(*shots):
    return SimpleNamespace(text=json.dumps({'shots': shots}, ensure_ascii=False))


@pytest.fixture
def llm():
    return Mock()


def invoke(llm, **fields):
    ctx = Mock(llm=llm)
    plugin.register(ctx)
    tool = ctx.register_tool.call_args.kwargs
    assert tool['name'] == tool['schema']['name'] == 'video_script_generate'
    return json.loads(tool['handler']({'body': BODY, **fields}))


@pytest.mark.parametrize('duration', [30, 60])
def test_registered_tool_returns_contiguous_shots_and_table(duration, llm):
    llm.complete.return_value = reply(shot(10, visual='放大 | 标题\n停留'), shot(duration - 10))
    args = {} if duration == 30 else {'duration_seconds': duration}
    result = invoke(llm, title='校稿', **args)
    assert result['duration_seconds'] == duration
    assert [(s['start_seconds'], s['end_seconds']) for s in result['shots']] == [(0, 10), (10, duration)]
    assert '放大 \\| 标题 停留' in result['markdown'] and '先核对标题' in result['markdown']
    assert len(result['markdown'].splitlines()) == 4
    llm.complete.assert_called_once()


@pytest.mark.parametrize('args', [{'body': '  '}, {'duration_seconds': 45}, {'duration_seconds': True},
                                  {'duration_seconds': 30.0}, {'title': []}])
def test_input_errors_precede_model_call(args, llm):
    assert 'error' in invoke(llm, **args)
    llm.complete.assert_not_called()


@pytest.mark.parametrize(('bad', 'message'), [
    (reply(shot(10)), '合计'), (reply(shot(True)), '正整数'), (reply(shot(0)), '正整数'),
    (reply(shot(30, source_quote='翻开目录')), '逐字'), (reply(shot(30, source_quote='')), 'source_quote'),
    (reply(shot(30, subtitle='')), 'subtitle'), (reply(shot(1), shot(29, voiceover='字' * 150)), '镜头 2'),
    (SimpleNamespace(text='不是 JSON'), 'JSON'), (reply(), '非空镜头列表'),
])
def test_invalid_script_gets_one_targeted_revision(bad, message, llm):
    llm.complete.side_effect = [bad, reply(shot(30))]
    assert 'markdown' in invoke(llm)
    correction = json.loads(llm.complete.call_args.args[0][1]['content'])
    assert correction['previous'] == bad.text
    assert message in correction['revision_request']
    assert correction['body'] == BODY and correction['duration_seconds'] == 30


def test_failed_revision_returns_reason_and_no_partial_result(llm):
    llm.complete.return_value = reply(shot(8))
    result = invoke(llm)
    assert set(result) == {'error'} and '修订后' in result['error'] and '合计 8 秒' in result['error']
    assert llm.complete.call_count == 2


def test_provider_error_skips_revision(llm):
    llm.complete.side_effect = ValueError('服务不可用')
    assert '服务不可用' in invoke(llm)['error']
    llm.complete.assert_called_once()
