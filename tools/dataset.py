"""Dependency-free unpack, verify and package tool for the public final dataset."""
import argparse
import gzip
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

NAMES=['players','events','stages','entrants','formations','lineup_members','encounters',
       'standings','records','sources','source_records']


def digest(raw):return hashlib.sha256(raw).hexdigest()
def json_bytes(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')


def inputs(root, verify=True):
    root=Path(root)
    dataset=json.loads((root/'dataset.json').read_text(encoding='utf-8'))
    if dataset.get('schema')!='YSTV-Final-Data-v1':raise ValueError('不兼容的最终数据格式。')
    expected={'LICENSE',*(f'data/{name}.json' for name in NAMES)}
    if dataset.get('files') and set(dataset['files'])!=expected:raise ValueError('最终数据文件清单不完整。')
    result={}
    for name in sorted(expected):
        entry=dataset.get('files',{}).get(name)
        candidates=[p for p in [name,name+'.gz'] if (root/p).is_file()]
        if len(candidates)!=1:raise ValueError('最终文件缺失或重复：'+name)
        storage=entry['storage'] if entry else candidates[0]
        if storage not in [name,name+'.gz']:raise ValueError('数据存储路径无效。')
        raw=(root/storage).read_bytes()
        if storage.endswith('.gz'):raw=gzip.decompress(raw)
        if verify and entry and (digest(raw)!=entry['sha256'] or len(raw)!=entry['size']):
            raise ValueError('文件校验失败：'+name)
        result[name]=raw
    return dataset,result


def write_repository(destination, files, metadata):
    destination=Path(destination)
    if destination.exists():raise ValueError('输出目录已存在，请使用新目录。')
    destination.mkdir(parents=True)
    metadata={key:value for key,value in metadata.items() if key not in ['files','version','counts']}
    for name,raw in files.items():
        storage=name+'.gz' if len(raw)>40*1024*1024 else name
        target=destination/storage;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(gzip.compress(raw,mtime=0) if storage.endswith('.gz') else raw)
    (destination/'dataset.json').write_bytes(json_bytes(metadata))
    return metadata


def package(repository, output, version, source_commit=None):
    if not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',version):raise ValueError('版本标签无效。')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    target=output/'ystv-data.zip'
    if target.exists():raise ValueError('数据包已存在，不覆盖正式版本。')
    dataset,files=inputs(repository)
    files['dataset.json']=json_bytes(dataset)
    manifest={'schema':'YSTV-Reviewed-Package-v1','files':{
        name:dict(size=len(raw),sha256=digest(raw)) for name,raw in files.items()}}
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        archive.writestr('package.json',json_bytes(manifest))
        for name,raw in files.items():archive.writestr(name,raw)
    release=dict(package=target.name,sha256=digest(target.read_bytes()),size=target.stat().st_size,license='MIT')
    return release


def validate_rows(files):
    """Validate stable IDs and relationships before making a candidate release."""
    data={name:json.loads(files[f'data/{name}.json']) for name in NAMES}
    keys={'players':'player_id','events':'competition_id','stages':'stage_id','entrants':'entrant_id',
          'formations':'formation_id','sources':'source_id','encounters':'encounter_id','source_records':'record_id'}
    ids={}
    for name,key in keys.items():
        values=[row[key] for row in data[name]]
        if len(values)!=len(set(values)) or any(not isinstance(v,str) or not v for v in values):
            raise ValueError('数据 ID 无效或重复：'+name)
        ids[name]=set(values)
    def ref(table,uid,nullable=False):
        if uid is None and nullable:return
        if uid not in ids[table]:raise ValueError(f'引用不存在：{table}/{uid}')
    for row in data['stages']:ref('events',row['competition_id'])
    tiers={'S','A','B','C','D','X','U'}
    for row in data['events']+data['stages']:
        if row.get('tier') not in tiers:raise ValueError('赛事或阶段等级无效。')
    for row in data['stages']:
        if row.get('honor_tier') not in tiers|{None}:raise ValueError('阶段荣誉等级无效。')
    stage_events={row['stage_id']:row['competition_id'] for row in data['stages']}
    entrant_stages={row['entrant_id']:row['stage_id'] for row in data['entrants']}
    for row in data['entrants']+data['formations']:
        ref('stages',row['stage_id']);ref('events',row['competition_id']);ref('players',row['player_id'],True)
        if row['competition_id']!=stage_events[row['stage_id']]:raise ValueError('阶段与赛事不一致。')
    for row in data['formations']:ref('entrants',row['entrant_id'])
    for row in data['encounters']:
        ref('stages',row['stage_id']);ref('sources',row['source']['source_id'])
        for side in ['a','b']:
            ref('players',row[side+'_player_id'],True);ref('entrants',row[side+'_entrant_id'])
            if entrant_stages[row[side+'_entrant_id']]!=row['stage_id']:raise ValueError('交手双方必须属于同一阶段。')
        if row['outcome'] not in ['a_win','b_win','draw',None]:raise ValueError('赛果无效。')
    for table in data['standings']['tables']:
        ref('stages',table['stage_uid']);ref('events',table['event_uid'])
        for row in table['entries']:
            ref('players',row['player_uid'],True)
            if row['rank_low']<1 or row['rank_high']<row['rank_low']:raise ValueError('名次区间无效。')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    check=sub.add_parser('verify');check.add_argument('--repository',type=Path,default=Path(__file__).resolve().parents[1])
    unpack=sub.add_parser('unpack');unpack.add_argument('--destination',required=True,type=Path)
    unpack.add_argument('--repository',type=Path,default=Path(__file__).resolve().parents[1])
    pack=sub.add_parser('pack');pack.add_argument('--input',required=True,type=Path)
    pack.add_argument('--output',required=True,type=Path);pack.add_argument('--version',default='manual')
    sync=sub.add_parser('sync');sync.add_argument('--input',required=True,type=Path)
    sync.add_argument('--repository',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args()
    if args.action in ['verify','unpack']:
        dataset,files=inputs(args.repository);validate_rows(files)
        if args.action=='unpack':
            if args.destination.exists():raise ValueError('解包目录已存在。')
            args.destination.mkdir(parents=True)
            for name,raw in files.items():
                target=args.destination/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            (args.destination/'dataset.json').write_bytes(json_bytes(dataset))
        print('最终数据文件、指纹与关联校验通过。');return
    if args.action=='sync':
        metadata=json.loads((args.input/'dataset.json').read_text(encoding='utf-8'))
        files={f'data/{name}.json':(args.input/'data'/(name+'.json')).read_bytes() for name in NAMES}
        files['LICENSE']=(args.input/'LICENSE').read_bytes();validate_rows(files)
        temp=args.repository.parent/(args.repository.name+'-sync-pending')
        write_repository(temp,files,metadata)
        try:
            for name in files:
                for storage in [name,name+'.gz']:
                    source=temp/storage;target=args.repository/storage
                    if source.exists():
                        target.parent.mkdir(parents=True,exist_ok=True)
                        if not target.exists() or target.read_bytes()!=source.read_bytes():shutil.copy2(source,target)
                    elif target.exists():target.unlink()
            shutil.copy2(temp/'dataset.json',args.repository/'dataset.json')
        finally:shutil.rmtree(temp)
        print('已将修改同步回仓库；请检查 Git 差异并提交到 main。');return
    dataset=json.loads((args.input/'dataset.json').read_text(encoding='utf-8'))
    files={f'data/{name}.json':(args.input/'data'/(name+'.json')).read_bytes() for name in NAMES}
    files['LICENSE']=(args.input/'LICENSE').read_bytes();validate_rows(files)
    repository=args.output/'repository'
    dataset['version']=args.version
    dataset['counts']={'players':sum(row['is_player'] for row in json.loads(files['data/players.json'])),
                       'events':len(json.loads(files['data/events.json'])),
                       'matches':len(json.loads(files['data/encounters.json'])),
                       'sources':len(json.loads(files['data/sources.json']))}
    dataset.pop('files',None)
    write_repository(repository,files,dataset)
    original=Path(__file__).resolve().parents[1]
    for name in ['README.md','.gitattributes','.gitignore']:
        if (original/name).exists():shutil.copy2(original/name,repository/name)
    (repository/'tools').mkdir()
    shutil.copy2(__file__,repository/'tools'/'dataset.py')
    print(json.dumps(package(repository,args.output,args.version),ensure_ascii=False))


if __name__=='__main__':main()
