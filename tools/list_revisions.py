import glob, re
files=glob.glob('migrations/versions/*.py')
res=[]
for f in sorted(files):
    s=open(f,encoding='utf-8').read()
    rev=re.search(r"revision\s*=\s*['\"]([0-9a-f]+)['\"]",s)
    down=re.search(r"down_revision\s*=\s*['\"]([0-9a-f]+)['\"]",s)
    res.append((f.split('\\')[-1], rev.group(1) if rev else None, down.group(1) if down else None))
for a,b,c in res:
    print(f"{a}: rev={b} down={c}")

