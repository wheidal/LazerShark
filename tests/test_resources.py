import os

import pytest

import resources


@pytest.mark.parametrize('platform, appdata, expected', [
    ('win32', 'APPDATA', ('APPDATA', 'LazerSharkKillKill')),
    ('darwin', 'APPDATA', ('home', 'Library', 'Application Support', 'LazerSharkKillKill')),
    ('linux', None, ('home', '.config', 'LazerSharkKillKill')),
])
def test_a_packaged_game_saves_where_each_system_expects(monkeypatch, tmp_path, platform, appdata, expected):
    monkeypatch.setattr(resources, 'FROZEN', True)
    monkeypatch.setattr(resources.sys, 'platform', platform)
    monkeypatch.setenv('HOME', str(tmp_path / 'home'))
    if appdata:
        monkeypatch.setenv('APPDATA', str(tmp_path / appdata))
    else:
        monkeypatch.delenv('APPDATA', raising=False)
    path = resources.settings_path('high_scores.json')
    assert path == os.path.join(tmp_path, *expected, 'high_scores.json')
    assert os.path.isdir(os.path.dirname(path))


def test_running_from_source_keeps_settings_beside_the_code():
    assert resources.settings_path('x.json') == os.path.join(resources.BASE_DIR, 'x.json')
