"""Marca la grilla de casillas del living (tema big_bang) y la guarda en theme.json.

La grilla sale de ajustar las líneas entre baldosas del fondo de día alineado;
el piso, los muebles que bloquean y los lugares están dibujados a mano en píxeles de aligned/.
Correr desde E:\ProyectosIA:  python -I "Assets BBTheory/mark_grid.py"
"""
import sys,json,re
sys.path.insert(0,'Assets BBad/tools')
import numpy as np,cv2
from grid import IsoGrid,tiles_to_rows
sA,pA,phA=0.5,21.2,2.575; sB,pB,phB=0.49,20.9,14.36
def corner(a,b):
    cA=phA+a*pA; cB=phB+b*pB; x=(cB-cA)/(sA+sB); return np.array([x,cA+sA*x])
o=corner(0,0); u=corner(1,0)-o; v=corner(0,1)-o
grid={"origin":[round(float(x),2) for x in o],"u":[round(float(x),3) for x in u],"v":[round(float(x),3) for x in v]}
# Borde del piso: base de las paredes y frente de la mesada/heladera de la cocina.
# Incluye el pasillo a los cuartos: la franja bajo la ventana de la derecha, hasta la heladerita verde.
floor=[(252,490),(684,703),(1106,493),(1106,482),(1032,420),(1018,415),(968,410),(942,404),(940,418),(902,420),
 (870,392),(846,392),(846,326),(838,321),(775,351),(762,342),(752,337),(720,337),(706,330),(655,338),(605,338),(590,316),(545,318),(500,340),(470,346),
 (335,416),(335,466),(272,485)]
# Muebles: solo la huella sobre el piso (lo que hay detrás también se camina)
blockers={
 'couch':[(410,415),(530,360),(572,385),(572,405),(455,455),(415,445)],
 'side_table':[(555,368),(600,358),(605,392),(565,397)],
 'armchair':[(600,390),(655,362),(690,382),(690,410),(645,432),(600,412)],
 'coffee_table':[(518,445),(555,428),(592,445),(555,466)],
 'chair':[(588,478),(615,465),(630,482),(600,495)],
 'box':[(400,440),(425,428),(445,440),(445,460),(420,466),(400,455)],
 'coat_rack_l':[(405,538),(432,538),(432,556),(405,556)],
 'coat_rack_r':[(670,672),(697,672),(697,690),(670,690)],
 'front_desks':[(458,552),(838,552),(838,610),(458,610)],
 'island':[(905,462),(985,458),(1020,550),(940,555)],
 'stool':[(876,488),(906,488),(906,512),(876,512)],
 'column':[(686,372),(718,372),(718,400),(686,400)],
 'minifridge':[(843,398),(886,398),(886,428),(843,428)],
 'trash':[(872,420),(902,420),(902,442),(872,442)],
 'dna':[(518,312),(538,312),(538,332),(518,332)],
 'bin':[(645,312),(668,312),(668,334),(645,334)],
 'side_bookcase':[(268,470),(335,455),(335,490),(268,495)],
}
def inside(poly,p): return cv2.pointPolygonTest(np.array(poly,np.float32),(float(p[0]),float(p[1])),False)>=0
g=IsoGrid({"grid":grid})
walk=set()
for a in range(-33,36):
    for b in range(-1,69):
        c=g.center(a,b)
        if inside(floor,c) and not any(inside(p,c) for p in blockers.values()): walk.add((a,b))
# solo lo conectado con la puerta
# Objetos agregados (no están en el fondo): imagen en props/, casilla que ocupan y punto de la imagen
# que va en el centro de esa casilla (los pies). Se dibujan sobre el fondo y bloquean su casilla.
PROPS={"whiteboard":{"image":"props/whiteboard.png","tile":(1,38),"feet":(22,94)}}
for pr in PROPS.values(): walk.discard(pr["tile"])
from collections import deque
seed=g.tile_at(497,346); comp={seed}; q=deque([seed])
while q:
    a,b=q.popleft()
    for n in ((a+1,b),(a-1,b),(a,b+1),(a,b-1)):
        if n in walk and n not in comp: comp.add(n); q.append(n)
print('puerta en', seed, 'caminable' if seed in walk else 'NO caminable', '- sueltas descartadas:', len(walk-comp)); walk=comp
# lugares: punto en el fondo -> casilla
pts={"door":((497,346),"down_right"),"hallway":((843,331),"up_right"),
     "window":((600,345),"up_right"),"center":((540,485),"down_right")}
places={k:{"tile":list(g.tile_at(*p)),"facing":f} for k,(p,f) in pts.items()}
# Sillón: tres asientos sobre el mueble, mirando abajo-derecha (casilla libre en b+1)
# El sillón ocupa 6 casillas de frente (b=31, a=5..10): un asiento por almohadón, con los pies en la casilla del frente
for k,t in (("couch_left",(10,31)),("couch_mid",(8,31)),("couch_right",(6,31))):
    assert inside(blockers['couch'],g.center(*t)) and (t[0],t[1]+1) in walk, (k,t)
    places[k]={"tile":list(t),"facing":"down_right"}
# Pizarrón: se escribe parado delante (la cara mira hacia abajo-izquierda, +a), mirándolo
wt=PROPS["whiteboard"]["tile"]; places["whiteboard"]={"tile":[wt[0]+1,wt[1]],"facing":"up_right"}
# Sillas de las compus (detrás de cada escritorio) y banqueta de la barra
# feet: dónde van los pies sentado si no es el centro de la casilla (offset en píxeles). En las sillas
# quedan debajo del escritorio (lo tapa la capa) y la cadera sobre el asiento.
for k,p,f,feet in (("desk_left",(523,512),"down_right",(535,556)),("desk_right",(755,510),"down_right",(767,556)),
                   ("kitchen",(898,535),"down_right",None)):
    places[k]={"tile":list(g.tile_at(*p)),"facing":f}
    if feet:
        c=g.center(*places[k]["tile"]); places[k]["offset"]=[feet[0]-c[0],feet[1]-c[1]]
    walk.discard(tuple(places[k]["tile"]))
# conectividad
start=tuple(places["door"]["tile"]); g.walkable=walk
for k,pl in places.items(): 
    p=g.path(start,tuple(pl["tile"])); print('  puerta ->',k, 'sin camino' if p is None else f'{len(p)} pasos')
# Huella de cada mueble en casillas (por fila, como tiles): la usa el orden de dibujo de las capas
footprints={}
for k,poly in blockers.items():
    t=[(a,b) for a in range(-33,36) for b in range(-1,69) if inside(poly,g.center(a,b))]
    if not t: t=[g.tile_at(*np.mean(poly,axis=0))]
    footprints[k]=tiles_to_rows(t)
th='Assets BBTheory/theme.json'; s=open(th,encoding='utf-8').read(); data=json.loads(s)
sc=data["scene"]
new={"_comment":"Grilla isométrica tipo Habbo sobre aligned/ (1372x764), siguiendo las baldosas del piso (~42x21 px). origin = esquina de la casilla (0,0); u = un paso en a (abajo-izquierda), v = un paso en b (abajo-derecha). tiles: casillas caminables por fila a -> [[b0,b1]]. Lugares = casilla + dirección; pueden ser no caminables (asiento, silla) y solo se usan como destino.",
     "sprite_scale":sc["sprite_scale"],"grid":grid,"tiles":tiles_to_rows(walk),"places":places,
     "seats":{"_comment":"Grupos de asientos: un rol que apunta al grupo va al asiento del personaje (owners) o al primero libre.",
              "couch":["couch_left","couch_mid","couch_right"],"desk":["desk_left","desk_right"]},
     "owners":{"couch_right":"sheldon","desk_right":"sheldon","desk_left":"leonard"},
     "prefers":{"_comment":"Asientos que le gustan a alguien sin ser suyos: los toma si están libres (Penny se sienta en el lugar de Sheldon).",
                "penny":["couch_right"]},
     "footprints":footprints,
     "props":{k:{"image":pr["image"],"pos":[g.center(*pr["tile"])[0]-pr["feet"][0],g.center(*pr["tile"])[1]-pr["feet"][1]],
                 "tiles":tiles_to_rows([pr["tile"]])} for k,pr in PROPS.items()}}
for k,v in sc.items(): new.setdefault(k,v)   # layers (cut_layers.py), effects y lo que no se marca acá
data["scene"]=new
txt=json.dumps(data,indent=2,ensure_ascii=False)
# filas de tiles en una línea cada una
txt=re.sub(r'\[\s+(-?\d+(?:\.\d+)?),\s+(-?\d+(?:\.\d+)?)\s+\]',r'[\1, \2]',txt)
txt=re.sub(r'\[\s+(\[[^\[\]]*\](?:,\s+\[[^\[\]]*\])*)\s+\]',lambda m:'['+re.sub(r'\s+',' ',m.group(1))+']',txt)
open(th,'w',encoding='utf-8').write(txt+"\n"); print(len(walk),'casillas caminables')
