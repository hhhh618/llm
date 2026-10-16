#!/usr/bin/env python3
"""Prepare matching Codex/Claude versions and a changelog; never push or install."""
import argparse
from datetime import date
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def semver(value):
    if not re.fullmatch(r'(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)', value):
        raise ValueError('Version must be a stable MAJOR.MINOR.PATCH')
    return tuple(int(part) for part in value.split('.'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version')
    parser.add_argument('--note', required=True)
    args = parser.parse_args()
    try:
        wanted = semver(args.version)
        paths = [ROOT / '.codex-plugin/plugin.json', ROOT / '.claude-plugin/plugin.json']
        manifests = [json.loads(path.read_text()) for path in paths]
        if len({item['name'] for item in manifests}) != 1 or len({item['version'] for item in manifests}) != 1:
            raise ValueError('Host manifests must have matching names and versions before release')
        if wanted <= semver(manifests[0]['version']):
            raise ValueError('New version must be greater than the current version')
        if not args.note.strip():
            raise ValueError('A nonempty change note is required')
        changelog = ROOT / 'CHANGELOG.md'
        heading, body = changelog.read_text().split('\n', 1)
        notes = f'{heading}\n\n## {args.version} - {date.today().isoformat()}\n\n- {args.note.strip()}\n' + body
        for path, manifest in zip(paths, manifests):
            manifest['version'] = args.version
            path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        changelog.write_text(notes)
        print(json.dumps({'prepared_plugin': manifests[0]['name'], 'version': args.version, 'suggested_tag': f"{manifests[0]['name']}-v{args.version}", 'next': 'Review diff, run tools/check_plugin.py, then commit, push and publish the tag/release'}, ensure_ascii=False))
    except (OSError, ValueError, KeyError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
