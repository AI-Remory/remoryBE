import glob,re
files=glob.glob('migrations/versions/*.py')
rev_map={}
downs=set()
for f in files:
    s=open(f,encoding='utf-8').read()
    rev=re.search(r"revision\s*=\s*['\"]([0-9a-f]+)['\"]",s)
    # down_revision may be a single quoted id or a tuple: ('a','b')
    down_single=re.search(r"down_revision\s*=\s*['\"]([0-9a-f]+)['\"]",s)
    down_tuple=re.search(r"down_revision\s*=\s*\(([^\)]+)\)",s)
    r=rev.group(1) if rev else None
    d=None
    if down_single:
        d=down_single.group(1)
    elif down_tuple:
        # extract all quoted ids in the tuple
        ids=re.findall(r"['\"]([0-9a-f]+)['\"]", down_tuple.group(1))
        d=tuple(ids)
    if r:
        rev_map[r]=d
    if d:
        if isinstance(d, tuple):
            for dd in d:
                downs.add(dd)
        else:
            downs.add(d)
heads=[r for r in rev_map.keys() if r not in downs]
print('heads:',heads)
for k in sorted(rev_map.keys()):
    print(k,'->',rev_map[k])


