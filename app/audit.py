from collections import defaultdict

def quality_assessment(movie:dict):
    flags=[]; score=100
    if not movie.get('analyzed'): return ['Métadonnées non analysées'],0
    h=int(movie.get('height') or 0); br=int(movie.get('video_bitrate') or 0); ch=int(movie.get('audio_channels') or 0)
    subs=str(movie.get('subtitle_languages') or '').strip(); codec=str(movie.get('video_codec') or '').upper()
    if h and h<720: flags.append('Résolution SD'); score-=35
    elif h==720: flags.append('Résolution 720p'); score-=15
    if ch and ch<=2: flags.append('Audio stéréo'); score-=8
    if not subs: flags.append('Aucun sous-titre'); score-=8
    if h>=1080 and br and br<2_500_000: flags.append('Bitrate vidéo faible'); score-=20
    if codec in {'MPEG4','MSMPEG4V3','WMV3'}: flags.append('Codec vidéo ancien'); score-=12
    if not movie.get('duration'): flags.append('Durée inconnue'); score-=30
    return flags,max(0,score)

def _bits(hexstr): return bin(int(hexstr,16))[2:].zfill(len(hexstr)*4)
def _hash_similarity(a,b):
    if len(a)!=len(b): return 0.0
    try:
        ba,bb=_bits(a),_bits(b); return 1-sum(x!=y for x,y in zip(ba,bb))/len(ba)
    except Exception: return 0.0

def dna_similarity(dna1,dna2):
    try:
        a=dna1.split(':',2)[2].split('|'); b=dna2.split(':',2)[2].split('|')
    except Exception: return 0.0
    if not a or len(a)!=len(b): return 0.0
    return sum(_hash_similarity(x,y) for x,y in zip(a,b))/len(a)

def duplicate_groups(movies:list[dict]):
    candidates=defaultdict(list)
    for m in movies:
        dur=float(m.get('duration') or 0)
        if dur>0 and m.get('video_dna'): candidates[round(dur/30)*30].append(m)
    links=[]
    for bucket,items in candidates.items():
        nearby=items+candidates.get(bucket-30,[])+candidates.get(bucket+30,[])
        for i,a in enumerate(items):
            for b in nearby:
                if int(a['id'])>=int(b['id']): continue
                da=float(a.get('duration') or 0); db=float(b.get('duration') or 0)
                if abs(da-db)>max(12,da*0.015): continue
                sim=dna_similarity(a.get('video_dna',''),b.get('video_dna',''))
                if sim>=0.90: links.append((int(a['id']),int(b['id']),sim))
    parent={}
    def find(x):
        parent.setdefault(x,x)
        if parent[x]!=x: parent[x]=find(parent[x])
        return parent[x]
    def union(a,b):
        ra,rb=find(a),find(b)
        if ra!=rb: parent[rb]=ra
    for a,b,_ in links: union(a,b)
    roots=defaultdict(list)
    for x in parent: roots[find(x)].append(x)
    groups={}; scores={}; n=1
    for ids in roots.values():
        if len(ids)<2: continue
        name=f'DNA-{n:04d}'; n+=1
        for x in ids: groups[x]=name
        for a,b,s in links:
            if a in ids and b in ids:
                scores[a]=max(scores.get(a,0),s); scores[b]=max(scores.get(b,0),s)
    return groups,scores
