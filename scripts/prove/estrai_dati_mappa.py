import json,sys
t=open('mappa_torino.html',encoding='utf-8').read().split('\n')
l=[x for x in t if x.startswith('const DATI = ')][0]
d=json.loads(l[len('const DATI = '):].rstrip(';'))
json.dump(d,open(sys.argv[1],'w'),separators=(',',':'),ensure_ascii=False)
print({k:len(json.dumps(v,separators=(',',':'),ensure_ascii=False)) for k,v in d.items()})
