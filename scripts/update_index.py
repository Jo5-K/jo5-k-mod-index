"""Generate the G1R schema v1 feed, retaining projects without ZIP releases."""
import base64, datetime, json, os, pathlib, urllib.request
ROOT = pathlib.Path(__file__).resolve().parents[1]
PROJECTS = [
 ('Jo5-K/2d-battle-menu-jo5-k', 'battle_menu_2d_jo5k', 'Interface de batalha, cenários, iluminação e toque. / Battle UI, scenery, lighting and touch.'),
 ('Jo5-K/glass-menu-jo5-k', 'glass_menu_jo5k', 'Temas dos menus fora da batalha. / Field menu themes.'),
 ('Jo5-K/rematch-gen3-Jo5-k', 'rematch_gen3', 'Revanches opcionais com treinadores. / Optional trainer rematches.'),
 ('Jo5-K/Hoenn-PT-BR-Jo5-k', 'hoenn_ptbr_jo5k', 'Tradução PT-BR de Hoenn; requer FRLG PT-BR instalado. / Hoenn translation; requires installed FRLG PT-BR resources.'),
 ('Jo5-K/2.5D-Battle-Menu-Jo5-k', 'battle_menu_25d_jo5k', 'Projeto 2.5D com profundidade e paralaxe; sem release. / 2.5D depth and parallax project; no release yet.'),
 ('Jo5-K/Qol-Jo5-k', 'qol_jo5k', 'Em desenvolvimento, sem versão instalável. / In development, no installable release yet.'),
]

def api(path):
 headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'Jo5-K-Mod-Index'}
 token = os.getenv('GH_TOKEN') or os.getenv('GITHUB_TOKEN')
 if token: headers['Authorization'] = 'Bearer ' + token
 with urllib.request.urlopen(urllib.request.Request('https://api.github.com/' + path, headers=headers), timeout=60) as response:
  return json.load(response)

def generate():
 entries = []
 for repo, id, summary in PROJECTS:
  releases = [r for r in api('repos/' + repo + '/releases?per_page=100') if not r['draft']]
  releases.sort(key=lambda r: r.get('published_at') or '', reverse=True)
  release = next((r for r in releases if any(a['name'].lower().endswith('.zip') and a['state']=='uploaded' for a in r['assets'])), None)
  if id in ('qol_jo5k','battle_menu_25d_jo5k') and not release:
   # Listing metadata only: no fabricated manifest, version or download.
   manifest = dict(name='Qol - Jo5-k' if id=='qol_jo5k' else '2.5D Battle Menu - Jo5-k', games=['firered','leafgreen','ruby','sapphire','emerald'], category='GAMEPLAY' if id=='qol_jo5k' else 'UI')
  else:
   path = 'hoenn_ptbr_jo5k/manifest.json' if id == 'hoenn_ptbr_jo5k' else 'manifest.json'
   manifest = json.loads(base64.b64decode(api('repos/' + repo + '/contents/' + path)['content']))
  entry = dict(id=id, folder=id, title=manifest['name'], author='Jo5-K', summary=summary,
   repo='https://github.com/' + repo, github=repo, games=manifest['games'],
   categories=[manifest.get('category','UI').upper()], tags=['gen3','jo5-k'],
   experimental=manifest.get('experimental',True), description_url='https://github.com/' + repo + '#readme')
  if release:
   asset = next(a for a in release['assets'] if a['name'].lower().endswith('.zip') and a['state']=='uploaded')
   version = release['tag_name'].removeprefix('v')
   entry.update(version=version, api=manifest['api'], game_version=manifest['game_version'], profile=manifest['profile'],
    permissions=manifest.get('permissions',[]), dependencies=manifest.get('dependencies',[]), conflicts=manifest.get('conflicts',[]),
    affects_link=manifest.get('affects_link',False), update_check='ok',
    first_release=min(r['published_at'] for r in releases if r.get('published_at')), last_release=release['published_at'],
    latest=dict(version=version, tag=release['tag_name'], name=release['name'], prerelease=release['prerelease'], published_at=release['published_at'],
     zip=dict(name=asset['name'], url=asset['browser_download_url'], size=asset['size'])))
  else:
   entry['summary'] += ' Sem release publicada. / No published release.'
   entry['tags'].append('em-desenvolvimento')
   entry['update_check'] = 'unavailable'
  entries.append(entry)
 path = ROOT / 'data/index.json'
 old = json.loads(path.read_text()) if path.exists() else {}
 now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
 doc = dict(schema_version=1, generated_at=old.get('generated_at',now) if old.get('mods')==entries else now,
  categories=['UI','GAMEPLAY','LANGUAGE'], base_games=['firered','leafgreen','ruby','sapphire','emerald'], mods=entries)
 for relative in ['data/index.json','site/data/index.json']:
  path = ROOT / relative
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
 print('Updated', len(entries), 'listed mods;', sum('latest' in e for e in entries), 'installable')

if __name__ == '__main__': generate()
