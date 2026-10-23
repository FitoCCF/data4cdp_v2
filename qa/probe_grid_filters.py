"""
Uso: python3 qa/probe_grid_filters.py  (con el backend en localhost:8000)

Prueba (solo GET) de todas las columnas de las grillas con el esquema nuevo: grid-values + grid_filters + ordering."""
import json, urllib.parse, urllib.request, urllib.error
B = 'http://localhost:8000/api/'
def get(ep, p):
    try:
        with urllib.request.urlopen(B + ep + '?' + urllib.parse.urlencode(p), timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {'_error': e.code, '_body': e.read().decode()[:200]}
H = ['equipment__area__plant__name', 'equipment__area__name', 'equipment__system__name']
VIEWS = {
 'Plantas': ('plants/', {}, ['id','tag','name','description']),
 'Sistemas': ('systems/', {}, ['id','tag','name','description']),
 'Áreas': ('areas/', {}, ['id','tag','name','description','plant']),
 'Equipos': ('equipments/', {}, ['id','tag','name','description','system','area']),
 'Muestras': ('samples/', {}, ['id','tag','name','equipment']),
 'Usuarios': ('users/', {}, ['id','nombre','apellido','email','rol','group']),
 'Grupos': ('userp/', {}, ['id','name']),
 'Tareas': ('tasks/', {}, ['id','task_catalog','duration','workers','frequency','start_date','description']+H+['equipment','procedure','turn']),
 'Programadas': ('taskp/', {}, ['id','task_id']+['task__'+h for h in H]+['task__equipment__name','year','week','day','date','group_id','estado_id','priority','completion_date','comments','rescheduled','reschedule_reason','reschedule_date','is_permanent_reschedule']),
 'Correctivas': ('correctivetasks/', {}, ['id','task_catalog','name']+H+['equipment','description','root_cause','creation_date','priority','created_by_user','turno']),
 'Ensayos (eq 2)': ('assays/', {'sample__equipment': 2}, ['id','date','time','instance','n1fe','n2cu','n3zn','n4mo','n5ech5','n6sc','n7ech7','pFe','pCu','pZn','pMo','pIns','pOx','pSol','tara','tweight','dweight','pweight','chemical_id','sample','a1fe','a2cu','a3zn','a4mo','a5a5','a6sol','a7a7','user','meta_user']),
}
fails, checked = [], 0
for view, (ep, base, fields) in VIEWS.items():
    total = get(ep, {**base, 'page_size': 1})['count']
    for fld in fields:
        gv = get(ep + 'grid-values/', {**base, 'field': fld})
        if '_error' in gv:
            fails.append((view, fld, 'grid-values', gv)); continue
        vals = gv['values']
        if not vals: continue
        counts = []
        for v in list(dict.fromkeys(vals[:2] + vals[-1:])):
            spec = {'in': [] if v == '' else [v], 'empty': v == ''}
            r = get(ep, {**base, 'grid_filters': json.dumps({fld: spec}), 'page_size': 1})
            if '_error' in r: fails.append((view, fld, f'filtro {v!r}', r)); continue
            counts.append(r['count'])
            if r['count'] == 0: fails.append((view, fld, f'filtro {v!r} devolvió 0', ''))
        # La suma por valor (sin repetir) debe cuadrar con el total cuando la lista no está truncada
        if not gv['truncated'] and len(vals) <= 3 and sum(counts) != total and '__' not in fld:
            fails.append((view, fld, f'suma {sum(counts)} != total {total}', ''))
        # Excluir el primer valor debe dar total - count(primero)
        if counts and not gv['truncated']:
            v = vals[0]
            spec = {'not_in': [], 'empty': True} if v == '' else {'not_in': [v]}
            r = get(ep, {**base, 'grid_filters': json.dumps({fld: spec}), 'page_size': 1})
            if '__' not in fld and r.get('count') != total - counts[0]:
                fails.append((view, fld, f'not_in {v!r}: {r.get("count")} != {total - counts[0]}', ''))
        o = get(ep, {**base, 'ordering': '-' + fld, 'page_size': 3})
        if '_error' in o: fails.append((view, fld, 'orden', o))
        checked += 1
for f in fails: print(' | '.join(map(str, f)))
print(f'{checked} columnas revisadas, {len(fails)} problemas')
