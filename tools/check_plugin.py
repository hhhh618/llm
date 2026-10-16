#!/usr/bin/env python3
"""Check the shared skills and the Codex/Claude plugin and marketplace metadata."""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
VERSION = re.compile(r'(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(relative):
    return json.loads((ROOT / relative).read_text())


def local_path(value):
    require(isinstance(value, str) and value.startswith('./'), f'Expected ./ path: {value!r}')
    path = (ROOT / value).resolve()
    require(path == ROOT or ROOT in path.parents, f'Path escapes plugin root: {value}')
    require(path.exists(), f'Missing path: {value}')
    return path


def main():
    codex = load('.codex-plugin/plugin.json')
    claude = load('.claude-plugin/plugin.json')
    require(codex['name'] == claude['name'], 'Plugin names differ between hosts')
    require(codex['version'] == claude['version'], 'Plugin versions differ between hosts')
    require(VERSION.fullmatch(codex['version']), 'Expected a stable MAJOR.MINOR.PATCH version')
    for manifest in (codex, claude):
        require(manifest.get('description') and manifest.get('author', {}).get('name'), 'Missing description or author')
    skill_root = local_path(codex['skills'])
    require(skill_root == ROOT / 'skills', 'Hosts must share the default skills directory')
    codex_market = load('.agents/plugins/marketplace.json')
    claude_market = load('.claude-plugin/marketplace.json')
    require(codex_market['name'] == claude_market['name'], 'Marketplace names differ between hosts')
    require(codex_market.get('interface', {}).get('displayName'), 'Missing Codex marketplace display name')
    require(claude_market.get('owner', {}).get('name'), 'Missing Claude marketplace owner')
    for catalog in (codex_market, claude_market):
        require(len(catalog['plugins']) == 1, 'Expected one root plugin in this marketplace')
        require(catalog['plugins'][0]['name'] == codex['name'], 'Marketplace/plugin name mismatch')
    codex_entry = codex_market['plugins'][0]
    require(codex_entry['source']['source'] == 'local', 'Expected a same-repository Codex source')
    require(local_path(codex_entry['source']['path']) == ROOT, 'Codex source must be the plugin root')
    require(local_path(claude_market['plugins'][0]['source']) == ROOT, 'Claude source must be the plugin root')
    require(codex_entry['policy']['installation'] == 'AVAILABLE', 'Unexpected installation policy')
    require(codex_entry['policy']['authentication'] == 'ON_INSTALL', 'Unexpected authentication policy')

    skills = sorted(skill_root.glob('*/SKILL.md'))
    require(skills, 'No packaged skills')
    for entry in skills:
        text = entry.read_text()
        require(text.startswith('---\n'), f'Missing frontmatter: {entry}')
        header = text.split('---', 2)[1]
        name = re.search(r'^name:\s*([a-z0-9-]+)\s*$', header, re.M)
        require(name and name.group(1) == entry.parent.name, f'Skill directory/name mismatch: {entry.parent.name}')
        require(re.search(r'^description:\s*\S', header, re.M), f'Missing skill description: {entry.parent.name}')
        vocabulary = entry.parent / 'resources/domain-vocabulary.json'
        if vocabulary.is_file():
            version = re.search(r'^\s+version:\s*[\"\x27]?(\d+\.\d+\.\d+)', header, re.M)
            require(version and json.loads(vocabulary.read_text())['skill_version'] == version.group(1), 'Skill/vocabulary version mismatch')
        for path in entry.parent.rglob('*.json'):
            json.loads(path.read_text())
        for path in entry.parent.rglob('*.md'):
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                target = target.split('#', 1)[0]
                if not target or '://' in target or target.startswith('mailto:'):
                    continue
                require((path.parent / target).exists(), f'Broken resource link: {path.relative_to(ROOT)} -> {target}')
    print(json.dumps({'status': 'valid', 'plugin': codex['name'], 'version': codex['version'], 'marketplace': codex_market['name'], 'skills': [p.parent.name for p in skills]}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'Plugin validation failed: {error}', file=sys.stderr)
        raise SystemExit(1)
