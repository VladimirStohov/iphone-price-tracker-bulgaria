"""Cloudflare Pages build command: python build.py; output: dist."""
import shutil,json
from pathlib import Path
root=Path(__file__).parent
out=root/'dist';out.mkdir(exist_ok=True)
for file in ['index.html','app.js','style.css','site.json','_headers']:
    shutil.copy2(root/file,out/file)
for path in (root/'data').glob('*.json'):
    json.loads(path.read_text(encoding='utf-8-sig'))
shutil.copytree(root/'data',out/'data',dirs_exist_ok=True)
print('Static site built in dist/')
