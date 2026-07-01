/* cerebro.js — Secuenciador de plegado con detección de choque (prototipo Node)
   ----------------------------------------------------------------------------
   Modelo: pieza = alas f[0..n-1] unidas por pliegues b[0..m-1] (m=n-1).
   Cada pliegue: ángulo interior a[i] y sentido d[i] ∈ {+1,-1} (arriba/abajo).
   Geometría real de útiles del DXF (matriz V=20 90°, punzón gooseneck).
   Busca el ORDEN de plegado que evita choques, probando permutaciones.        */

const DEG = Math.PI / 180;
function rot(p, th){ const c=Math.cos(th), s=Math.sin(th); return {x:p.x*c-p.y*s, y:p.x*s+p.y*c}; }

/* ---- geometría real de los útiles (mm; X=0 centro V, Y arriba+, 0=hombros) ---- */
const DIE = [[-75,-180.2],[-75,-168],[-88,-168],[-88,-148],[-75,-148],[-75,-103],[-12,-103],[-12,0],[-10,0],[0,-10],[10,0],[12,0],[12,-103],[75,-103],[75,-148],[88,-148],[88,-168],[75,-168],[75,-180.2]];
const PUNCH_SEGS = [[[-0.0,0.0],[-6.6,6.74]],[[-6.6,6.74],[-6.86,8.61]],[[-6.86,8.61],[-19.84,21.84]],[[-19.84,21.84],[-19.84,71.73]],[[-19.84,71.73],[-16.73,71.73]],[[-16.73,71.73],[-16.73,80.07]],[[-16.73,80.07],[-19.84,80.07]],[[-19.84,80.07],[-19.84,97.31]],[[-19.84,97.31],[-7.2,97.31]],[[-7.2,97.31],[-7.2,195.24]],[[-7.2,195.24],[21.8,195.24]],[[21.8,195.24],[21.8,116.24]],[[21.8,116.24],[6.8,116.24]],[[6.8,116.24],[6.8,67.24]],[[6.8,67.24],[5.8,67.24]],[[5.8,67.24],[5.8,42.87]],[[5.8,42.87],[5.81,6.52]],[[5.81,6.52],[-0.0,0.0]]];
const V = 20, DIE_HALF = 10, TABLE_HALF = 88;     // medio-V, medio ancho matriz
const X_MIN = 5, X_MAX = 600;                      // recorrido del tope (mm)

/* ---- penetración para el ángulo (plegado al aire) ---- */
function penetracion(alpha){ return (V/2)*Math.tan((180-alpha)/2*DEG); }

/* ---- intersección de segmentos ---- */
function segInt(a,b,c,d){
  function cr(o,p,q){ return (p.x-o.x)*(q.y-o.y)-(p.y-o.y)*(q.x-o.x); }
  const d1=cr(c,d,a), d2=cr(c,d,b), d3=cr(a,b,c), d4=cr(a,b,d);
  return ((d1>0&&d2<0)||(d1<0&&d2>0)) && ((d3>0&&d4<0)||(d3<0&&d4>0));
}

/* ---- perfil de la pieza en su estado actual (done = set de pliegues hechos) ----
   Devuelve puntos y la dirección (deg) de cada ala en coords locales.          */
function profile(fl, an, dr, done){
  const pts=[{x:0,y:0}]; const fdir=[]; let dir=0,x=0,y=0;
  for(let i=0;i<fl.length;i++){
    fdir.push(dir);
    x += fl[i]*Math.cos(dir*DEG); y += fl[i]*Math.sin(dir*DEG);
    pts.push({x,y});
    if(i<an.length && done[i]) dir += dr[i]*(180-an[i]);
  }
  return {pts, fdir};
}

/* ---- coloca la pieza para plegar 'bi' en una de 4 orientaciones, y evalúa ---- */
function place(fl, an, dr, done, bi, mx, my, s){
  const {pts, fdir} = profile(fl, an, dr, done);
  const th = -fdir[bi]*DEG;                 // rota para que el ala bi quede horizontal
  const bp = rot(pts[bi+1], th);            // punto de pliegue rotado
  const rest = s;                            // la chapa apoya a la altura del espesor
  const P = pts.map(p=>{
    let q = rot(p, th);
    q = {x:q.x-bp.x, y:q.y-bp.y+rest};       // pliegue bi -> (0,rest)
    if(mx) q.x = -q.x;                        // espejo izq/der (qué extremo al tope)
    if(my) q.y = 2*rest - q.y;               // voltear la pieza (folds abajo->arriba)
    return q;
  });
  // segmentos de la chapa, marcando el ala actual (toca la punta = contacto natural)
  const segs=[];
  for(let i=0;i<fl.length;i++){
    segs.push({a:P[i], b:P[i+1], tip:(i===bi||i===bi+1), idx:i});
  }
  return {P, segs, rest};
}

/* ---- chequeos de factibilidad de una colocación ---- */
function feasible(pl, alpha, s){
  const pen = penetracion(alpha);
  const tipY = -pen;                          // punta del punzón al final del pliegue
  const punch = PUNCH_SEGS.filter(g=>Math.min(g[0][1],g[1][1])<=95)
                          .map(g=>[{x:g[0][0],y:g[0][1]+tipY},{x:g[1][0],y:g[1][1]+tipY}]);
  // 1) nada por debajo de la matriz en la zona del troquel (no se puede apoyar)
  for(const p of pl.P){ if(Math.abs(p.x) < TABLE_HALF && p.y < -1.0) return {ok:false, why:'una parte queda por debajo de la matriz'}; }
  // 2) choque con el punzón (excluye el ala que envuelve la punta)
  for(const sg of pl.segs){ if(sg.tip) continue;
    for(const q of punch){ if(segInt(sg.a, sg.b, q[0], q[1])) return {ok:false, why:'choque con el punzón'}; }
  }
  // 3) tope alcanzable: X = distancia horizontal del pliegue al punto más atrás
  //    (tope a -X). El tope contacta el punto de menor x de toda la pieza.
  let xl = Math.min.apply(null, pl.P.map(p=>p.x));
  const X = -xl;
  if(X < X_MIN) return {ok:false, why:'ala muy corta para el tope ('+X.toFixed(0)+' mm)'};
  if(X > X_MAX) return {ok:false, why:'fuera del recorrido del tope ('+X.toFixed(0)+' mm)'};
  return {ok:true, X};
}

/* ---- simula un ORDEN completo; devuelve pasos o el punto donde falla ---- */
function simulateOrder(fl, an, dr, order, s){
  const done = an.map(()=>false);
  const steps=[]; let prevOri=null, manips=0, collisions=0;
  for(let k=0;k<order.length;k++){
    const bi = order[k];
    let best=null, fallback=null;
    for(const mx of [false,true]) for(const my of [false,true]){
      const pl = place(fl, an, dr, done, bi, mx, my, s);
      const f = feasible(pl, an[bi], s);
      const ori=(mx?1:0)+(my?2:0);
      const cost = prevOri===null?0:(ori!==prevOri?1:0);
      if(f.ok){ if(!best || cost<best.cost) best={mx,my,ori,cost,X:f.X,ok:true}; }
      else if(ori===0){ fallback={mx,my,ori,cost:0,X:f.X||0,ok:false,why:f.why}; }
    }
    const chosen = best || fallback || {mx:false,my:false,ori:0,X:0,ok:false,why:'sin colocación'};
    if(!chosen.ok) collisions++;
    if(prevOri!==null && chosen.ori!==prevOri) manips++;
    prevOri=chosen.ori;
    steps.push({order:k+1, bend:bi, alpha:an[bi], X:chosen.X, mx:chosen.mx, my:chosen.my, ok:chosen.ok, why:chosen.why});
    done[bi]=true;
  }
  return {ok:collisions===0, collisions, steps, manips};
}

/* ---- permutaciones (hasta m! ; cap razonable) ---- */
function* perms(arr){
  if(arr.length<=1){ yield arr.slice(); return; }
  for(let i=0;i<arr.length;i++){
    const rest=arr.slice(0,i).concat(arr.slice(i+1));
    for(const p of perms(rest)) yield [arr[i]].concat(p);
  }
}

/* ---- BUSCAR ORDEN: prueba todas las permutaciones, elige la factible mejor ---- */
function buscarOrden(fl, an, dr, s){
  const m=an.length; const idx=[...Array(m).keys()];
  let best=null, feasibleCount=0, tried=0;
  for(const order of perms(idx)){
    tried++;
    const r=simulateOrder(fl, an, dr, order, s);
    if(r.collisions===0) feasibleCount++;
    // ranking: menos choques, luego menos manipuleos
    if(!best || r.collisions<best.collisions || (r.collisions===best.collisions && r.manips<best.manips))
      best={order, ...r};
    if(tried>40320) break;   // tope 8!
  }
  return {best, feasibleCount, tried};
}

/* =================== PRUEBAS =================== */
function test(name, fl, an, dr){
  const s=2;
  const res = buscarOrden(fl, an, dr, s);
  console.log('\n### '+name+'  alas='+fl.join('/')+'  ang='+an.join(',')+'  sent='+dr.join(','));
  console.log('  permutaciones probadas:', res.tried, ' órdenes sin choque:', res.feasibleCount);
  const b=res.best;
  console.log('  ORDEN elegido:', b.order.map(x=>'b'+x).join(' → '), ' manipuleos:', b.manips, b.collisions===0?'  ✓ sin choques':('  ⚠ '+b.collisions+' choque(s)'));
  b.steps.forEach(st=>console.log('   paso'+st.order+': pliegue b'+st.bend+' '+st.alpha+'°  X='+st.X.toFixed(1)+'  '+(st.mx?'[gira] ':'')+(st.my?'[voltea] ':'')+(st.ok?'':('⚠ '+st.why))));
}

test('U simple',        [50,80,50],   [90,90],    [1,1]);
test('U profunda angosta',[50,12,50], [90,90],    [1,1]);
test('Z (sentidos opuestos)',[40,60,40],[90,90],  [1,-1]);
test('Sombrero/hat',    [25,40,60,40,25],[90,90,90,90],[ -1,1,1,-1]);
test('Caja 4 lados',    [40,60,60,40],[90,90,90], [1,1,1]);
test('L simple',        [60,40],      [90],       [1]);
test('Canal con pestañas',[20,30,80,30,20],[90,90,90,90],[1,1,1,1]);
