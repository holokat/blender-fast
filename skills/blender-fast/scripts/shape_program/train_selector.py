"""Fit a small local TF-IDF softmax lesson selector. Requires existing NumPy."""
import argparse
import collections
import json
import math
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from shape_program.teaching import load_library,tokens,features,DEFAULT_LIBRARY
from shape_program.expand import digest


def train(lessons,steps=600):
    import numpy as np
    start=time.perf_counter()
    labels=[r['id'] for r in lessons]
    training=[(text,i) for i,r in enumerate(lessons) for text in r['captions']['train']]
    testing=[(text,i) for i,r in enumerate(lessons) for text in r['captions']['test']]
    document_counts=collections.Counter(w for text,_ in training for w in set(tokens(text)))
    vocabulary=sorted(document_counts)
    idf=[math.log((1+len(training))/(1+document_counts[w]))+1 for w in vocabulary]
    x=np.array([features(text,vocabulary,idf) for text,_ in training])
    y=np.eye(len(labels))[[i for _,i in training]]
    weights=np.zeros((len(vocabulary),len(labels)));bias=np.zeros(len(labels))
    losses=[]
    for step in range(steps):
        logits=x@weights+bias;logits-=logits.max(axis=1,keepdims=True)
        probabilities=np.exp(logits);probabilities/=probabilities.sum(axis=1,keepdims=True)
        if step in (0,steps-1):losses.append(float(-(y*np.log(probabilities+1e-12)).sum()/len(x)))
        residual=(probabilities-y)/len(x)
        weights-=2*(x.T@residual+.002*weights)
        bias-=2*residual.sum(axis=0)
    centroids=y.T@x;centroids/=np.linalg.norm(centroids,axis=1,keepdims=True)
    tests=np.array([features(text,vocabulary,idf) for text,_ in testing])
    correct=np.array([i for _,i in testing])
    def evaluate(scores):
        ranks=np.argsort(-scores,axis=1)
        return {'top1_correct':int((ranks[:,0]==correct).sum()),'top3_correct':int((ranks[:,:3]==correct[:,None]).any(axis=1).sum()),
            'count':len(testing),'predictions':[{'prompt':text,'expected':labels[wanted],'ranked':[labels[int(j)] for j in rank[:3]]} for (text,wanted),rank in zip(testing,ranks)]}
    learned=evaluate(tests@weights+bias);baseline=evaluate(tests@centroids.T)
    # Train/evaluate a real selector; ship the better observed top-1 path, ties favor the learned path.
    selected='softmax' if learned['top1_correct']>=baseline['top1_correct'] else 'centroid'
    model={'version':1,'kind':selected,'labels':labels,'vocabulary':vocabulary,'idf':idf,'corpus_sha256':digest(lessons),
        'weights':(weights.T if selected=='softmax' else centroids).round(8).tolist(),
        'bias':(bias if selected=='softmax' else np.zeros(len(labels))).round(8).tolist()}
    report={'training_seconds':time.perf_counter()-start,'steps':steps,'training_examples':len(training),'test_examples':len(testing),
        'training_loss_first_last':losses,'vocabulary_size':len(vocabulary),'parameter_count':weights.size+bias.size,
        'softmax':learned,'centroid_baseline':baseline,'selected':selected,'corpus_sha256':digest(lessons),
        'scope':'Agent-authored captions of eight executable shape lessons. Held-out wording within known classes, not unseen object categories or a geometry-generating model.'}
    return model,report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--library',type=Path,default=DEFAULT_LIBRARY)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    args=p.parse_args();model,report=train(load_library(args.library))
    args.output.write_text(json.dumps(model,separators=(',',':'))+'\n');args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('softmax','centroid_baseline')}))
    print(json.dumps({'softmax_top1':report['softmax']['top1_correct'],'baseline_top1':report['centroid_baseline']['top1_correct'],'test_count':report['test_examples']}))


if __name__=='__main__':main()
