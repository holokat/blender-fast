"""Executable lesson library, local selector inference, and program composition."""
import argparse
import collections
import json
import math
import re
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from shape_program.expand import expand,digest

DEFAULT_LIBRARY=Path(__file__).resolve().parents[2]/'assets/shape-lessons'
STOP=set('a an the and of with by in from on to for using build made'.split())


def tokens(text):
    return [w for w in re.findall(r'[a-z0-9]+',text.lower()) if w not in STOP]


def load_library(directory=DEFAULT_LIBRARY):
    lessons=[];seen=set();captions=set()
    for path in sorted(Path(directory).glob('*.json')):
        if path.name=='selector.json':continue
        row=json.loads(path.read_text())
        if not isinstance(row.get('id'),str) or row['id'] in seen:raise ValueError('Invalid or duplicate lesson id')
        expand(row['program'])
        seen.add(row['id'])
        for split in ('train','test'):
            texts=row['captions'][split]
            if not isinstance(texts,list) or not texts:raise ValueError('Each lesson needs train and held-out test captions')
            for text in texts:
                if not isinstance(text,str) or not tokens(text):raise ValueError('Empty caption')
                canonical=' '.join(tokens(text))
                if canonical in captions:raise ValueError('Duplicate caption across the training/evaluation corpus')
                captions.add(canonical)
        lessons.append(row)
    if len(lessons)<2:raise ValueError('At least two executable lessons are required')
    return lessons


def features(text,vocabulary,idf):
    counts=collections.Counter(tokens(text))
    values=[(1+math.log(counts[w]))*idf[i] if counts[w] else 0 for i,w in enumerate(vocabulary)]
    length=math.sqrt(sum(v*v for v in values)) or 1
    return [v/length for v in values]


def suggest(text,model,lessons,limit=3):
    if model['corpus_sha256']!=digest(lessons):raise ValueError('Selector is stale; retrain after changing lessons')
    x=features(text,model['vocabulary'],model['idf'])
    if not any(x):return []
    scores=[sum(a*b for a,b in zip(x,weights))+bias for weights,bias in zip(model['weights'],model['bias'])]
    ranking=sorted(range(len(scores)),key=lambda i:scores[i],reverse=True)[:limit]
    rows={r['id']:r for r in lessons}
    return [{'id':model['labels'][i],'summary':rows[model['labels'][i]]['summary'],'score':round(scores[i],5)} for i in ranking]


def compose(layout,lessons):
    """Expand a short layout using explicit lesson definitions; no text-to-scene claim."""
    definitions={};palette={}
    for lesson in lessons:
        for key,value in lesson['program']['definitions'].items():
            if key in definitions and definitions[key]!=value:raise ValueError('Conflicting lesson definitions')
            definitions[key]=value
        for key,value in lesson['program']['palette'].items():
            if key in palette and palette[key]!=value:raise ValueError('Conflicting lesson palettes')
            palette[key]=value
    definitions.update(layout.get('definitions',{}))
    needed=set()
    def need(key):
        if key in needed:return
        if key not in definitions:raise ValueError('No lesson definition named '+str(key))
        needed.add(key)
        def scan(nodes):
            for node in nodes:
                if node.get('op')=='call':need(node['use'])
                if 'children' in node:scan(node['children'])
        scan(definitions[key]['nodes'])
    for row in layout['assemblies']:need(row['use'])
    palette.update(layout.get('palette',{}))
    program=dict(layout,version=layout.get('version',1),palette=palette,definitions={k:definitions[k] for k in sorted(needed)})
    expand(program)
    return program


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--library',type=Path,default=DEFAULT_LIBRARY)
    sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('suggest');q.add_argument('prompt');q.add_argument('--model',type=Path);q.add_argument('--limit',type=int,default=3)
    q=sub.add_parser('compose');q.add_argument('layout',type=Path);q.add_argument('--output',type=Path,required=True)
    sub.add_parser('list')
    q=sub.add_parser('export');q.add_argument('--output',type=Path,required=True)
    args=p.parse_args();lessons=load_library(args.library)
    if args.command=='suggest':
        model=json.loads((args.model or args.library/'selector.json').read_text())
        print(json.dumps(suggest(args.prompt,model,lessons,args.limit),indent=2))
    elif args.command=='compose':
        program=compose(json.loads(args.layout.read_text()),lessons)
        args.output.write_text(json.dumps(program,indent=2)+'\n')
        print(json.dumps({'file':str(args.output),'program_sha256':digest(program),'source_bytes':args.layout.stat().st_size,'expanded_bytes':args.output.stat().st_size}))
    elif args.command=='export':
        with args.output.open('w') as f:
            for row in lessons:
                for split,texts in row['captions'].items():
                    for text in texts:
                        f.write(json.dumps({'lesson_id':row['id'],'split':split,'prompt':text,'program':row['program'],
                            'provenance':row['provenance'],'validation':'structural expansion passed; visual review is a separate gate'})+'\n')
        print(json.dumps({'examples':sum(len(r['captions'][s]) for r in lessons for s in ('train','test')),'corpus_sha256':digest(lessons)}))
    else:print(json.dumps([{'id':r['id'],'summary':r['summary'],'params':r['program']['definitions'][r['id']].get('params',{})} for r in lessons],indent=2))


if __name__=='__main__':main()
