"""Build a full official WRAPP only after hash-bound native acceptance."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from simready.manage.api import _relativize_validation_sidecar
from simready.package.api import Packager,PackageSpec
from simready.package.impl import bom as sdk_bom
from wrapp.utils.coro import force_wrapp_thread
from native_tool_findings import assess


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

async def sdk_phase(phase,root,logical):
    """Keep each documented SDK phase in one isolated WRAPP loop lifecycle."""
    staging=root/'package-staging'/logical
    name='simready.hf.PalatialSim.palatial-nv-asset-library.'+logical
    definition=root/'package-repository/.packages'/name/'2026.10.13_00/com.nvidia.simready.packaging.json'
    sdk_bom.hash_files=force_wrapp_thread(sdk_bom.hash_files)
    packager=Packager(config_path=root/'workspace/project_config.toml')
    if phase=='pre':
        result=await packager.pre_validate(str(staging),root_usds=['simready_usd/'+logical+'.usd'],write_metadata=True)
        receipt={'phase':phase,'passed':result.passed}
    elif phase=='create':
        from simready.package.impl.create_package import create_package
        result=await create_package(name,'2026.10.13_00','cc-by-4.0',str(staging),str(root/'package-repository'))
        if Path(result.pkg_def_url.replace('file://',''))!=definition:raise RuntimeError('SDK package output differs')
        receipt={'phase':phase,'passed':True,'package_definition':str(definition)}
    else:
        result=await packager.post_validate(str(definition),write_evidence=True)
        receipt={'phase':phase,'passed':result.passed}
    if not receipt['passed']:raise RuntimeError('Required SDK package phase failed')
    target=root/'package-phase-receipts'/logical;target.mkdir(parents=True,exist_ok=True)
    (target/(phase+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True,type=Path);parser.add_argument('--qualification',type=Path);parser.add_argument('--asset',required=True);parser.add_argument('--sdk-phase',choices=['pre','create','post'])
    args=parser.parse_args();root=args.root.resolve()
    if args.sdk_phase:return await sdk_phase(args.sdk_phase,root,args.asset)
    rows=json.loads(args.qualification.read_text());row=assess(next(r for r in rows if r['logical_asset']==args.asset),root)
    if row['native_status'] not in {'passed','completed_with_tool_findings'} or not row['safety_accepted'] or row['planned_test_count']!=row['result_count']:
        raise RuntimeError('Native qualification is incomplete')
    logical=row['logical_asset'];source=root/'workspace/content'/logical;usd=source/'simready_usd'/(logical+'.usd')
    if digest(usd)!=row['asset_usd_sha256']:raise RuntimeError('Native source revision differs')
    staging=root/'package-staging'/logical
    if staging.exists():raise FileExistsError('Use a fresh package staging folder')
    def copy(src,dest):
        if '.metadata' in Path(src).parts or '.thumbs' in Path(src).parts or Path(src).suffix in {'.usd','.usda','.usdc'}:
            return shutil.copy2(src,dest)
        os.link(src,dest);return dest
    shutil.copytree(source,staging,copy_function=copy)
    # Official submit retains JSON evidence and removes generated HTML reports.
    for path in (staging/'.metadata').rglob('*'):
        if path.is_file() and path.suffix.lower()!='.json':path.unlink()
    validation=staging/'.metadata'/(logical+'_validation.json')
    original_validation_hash=digest(validation)
    _relativize_validation_sidecar(validation,source)
    validation_hash=digest(validation)
    thumb=staging/'simready_usd/.thumbs/256x256'/(logical+'.usd.png')
    shutil.copy2(root/row['thumbnail']['path'],thumb)
    if digest(thumb)!=row['thumbnail']['sha256']:raise RuntimeError('Native thumbnail differs')
    spec=PackageSpec(name='simready.hf.PalatialSim.palatial-nv-asset-library.'+logical,
                     version='2026.10.13_00',license_id='cc-by-4.0',source=str(staging),
                     repo=str(root/'package-repository'),root_usds=['simready_usd/'+logical+'.usd'])
    # WRAPP's public storage calls already hash on its dedicated loop. The
    # package BOM helper also hashes on the caller loop, binding the singleton
    # CPU semaphore to two loops for large assets. Dispatch that exact,
    # unchanged helper to WRAPP's supported loop. Keep ContextManager entry on
    # the caller thread, as WRAPP initialization requires.
    sdk_bom_source_sha256=digest(Path(sdk_bom.__file__))
    phases={}
    for phase in ['pre','create','post']:
        subprocess.run([sys.executable,__file__,'--root',str(root),'--asset',logical,'--sdk-phase',phase],check=True)
        phases[phase]=json.loads((root/'package-phase-receipts'/logical/(phase+'.json')).read_text())
    definition=Path(phases['create']['package_definition'])
    if digest(usd)!=row['asset_usd_sha256'] or digest(definition.parent/'simready_usd'/(logical+'.usd'))!=row['asset_usd_sha256']:
        raise RuntimeError('Packaging changed the qualified USD revision')
    # The official API raises on either required validation failure.
    receipt={'asset':logical,'status':'completed','asset_usd_sha256':digest(usd),
             'package_definition':str(definition),'package_definition_sha256':digest(definition),
             'native_qualification':str(args.qualification),'native_qualification_sha256':digest(args.qualification),
             'original_validation_sha256':original_validation_hash,'normalized_validation_sha256':validation_hash,
             'thumbnail_sha256':digest(thumb),'pre_validation_passed':phases['pre']['passed'],
             'post_validation_passed':phases['post']['passed'],
             'packager_dispatch':{'bom_hashing_loop':'wrapp-thread','sdk_bom_source_sha256':sdk_bom_source_sha256,
                                  'isolated_sdk_phases':['pre','create','post'],
                                  'sdk_files_modified':False,'validation_or_hash_algorithms_modified':False}}
    if row.get('tool_findings'):receipt['tool_findings']=row['tool_findings']
    if not receipt['pre_validation_passed'] or not receipt['post_validation_passed']:raise RuntimeError('Official package validation failed')
    target=root/'package-receipts';target.mkdir(exist_ok=True);(target/(logical+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt),flush=True)


if __name__=='__main__':asyncio.run(main())
