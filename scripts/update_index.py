"""Generate the G1R schema v1 feed from published ZIP releases, including RCs."""
import datetime,json,os,pathlib,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
PROJECTS=[('Jo5-K/2d-battle-menu-jo5-k','battle_menu_2d_jo5k','Interface de batalha, cenários, iluminação e toque. / Battle UI, scenery, lighting and touch.'),('Jo5-K/glass-menu-jo5-k','glass_menu_jo5k','Temas dos menus fora da batalha. / Field menu themes.'),('Jo5-K/rematch-gen3','rematch_gen3','Revanches opcionais com treinadores. / Optional trainer rematches.')]
def api(path):
 headers={'Accept':'application/vnd.github+json','User-Agent':'Jo5-K-Mod-Index'}
 token=os.getenv('GH_TOKEN') or os.getenv('GITHUB_TOKEN')
 if token:headers['Authorization']='Bearer '+token
 with urllib.request.urlopen(urllib.request.Request('https://api.github.com/'+path,headers=headers),timeout=60) as r:return json.load(r)
def generate():
 entries=[]
 for repo,id,summary in PROJECTS:
  releases=[r for r in api('repos/'+repo+'/releases?per_page=100') if not r['draft']]
  releases.sort(key=lambda r:r.get('published_at') or '',reverse=True)
  release=next((r for r in releases if any(a['name'].lower().endswith('.zip') and a['state']=='uploaded' for a in r['assets'])),None)
  if not release:raise RuntimeError('No installable release for '+repo)
  asset=next(a for a in release['assets'] if a['name'].lower().endswith('.zip') and a['state']=='uploaded')
  import base64
  manifest=json.loads(base64.b64decode(api('repos/'+repo+'/contents/manifest.json')['content']))
  version=release['tag_name'].removeprefix('v')
  entries.append(dict(id=id,folder=id,title=manifest['name'],author='Jo5-K',version=version,summary=summary,
   repo='https://github.com/'+repo,github=repo,api=manifest['api'],game_version=manifest['game_version'],games=manifest['games'],
   categories=[manifest.get('category','UI').upper()],tags=['gen3','jo5-k'],profile=manifest['profile'],
   permissions=manifest.get('permissions',[]),dependencies=manifest.get('dependencies',[]),conflicts=manifest.get('conflicts',[]),
   affects_link=manifest.get('affects_link',False),experimental=manifest.get('experimental',False),
   description_url='https://github.com/'+repo+'#readme',update_check='ok',
   first_release=min(r['published_at'] for r in releases if r.get('published_at')),last_release=release['published_at'],
   latest=dict(version=version,tag=release['tag_name'],name=release['name'],prerelease=release['prerelease'],published_at=release['published_at'],
    zip=dict(name=asset['name'],url=asset['browser_download_url'],size=asset['size']))))
 # Keep generated_at stable when the listing itself has not changed.
 path=ROOT/'data/index.json'
 old=json.loads(path.read_text()) if path.exists() else {}
 now=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
 doc=dict(schema_version=1,generated_at=old.get('generated_at',now) if old.get('mods')==entries else now,categories=['UI','GAMEPLAY'],base_games=['firered','leafgreen','ruby','sapphire','emerald'],mods=entries)
 for relative in ['data/index.json','site/data/index.json']:
  p=ROOT/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
 print('Updated',len(entries),'installable mods')
if __name__=='__main__':generate()
