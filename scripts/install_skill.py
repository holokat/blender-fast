"""Install this repository's skill without modifying unrelated Codex settings."""
import argparse
import os
import shutil
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skills-dir',type=Path,help='Defaults to CODEX_HOME/skills or ~/.codex/skills')
    args=parser.parse_args()
    source=Path(__file__).resolve().parents[1]/'skills/blender-fast'
    codex=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))
    parent=args.skills_dir or codex/'skills';target=parent/'blender-fast'
    if target.exists():
        raise SystemExit(f'{target} already exists. Review and back up the existing skill before updating it.')
    parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(source,target,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.DS_Store'))
    print(f'Installed {target}')
    print('Automatic skill selection is enabled. For a required default, add the routing sentence documented in the repository README to your Codex AGENTS.md.')


if __name__=='__main__':main()
