"""Lightweight 3D header: rotating wireframe shield-globe with particles (three.js CDN)."""

HERO_HTML = """
<div id="hero" style="position:relative;width:100%;height:250px;border-radius:16px;overflow:hidden;
 background:radial-gradient(circle at 50% 40%,#1E3A8A 0%,#0B1220 75%);box-shadow:0 12px 30px rgba(15,23,42,.35)">
 <div style="position:absolute;bottom:14px;width:100%;text-align:center;z-index:2;
  font-family:sans-serif;color:#FFFFFF;font-size:30px;font-weight:800;letter-spacing:1px;
  text-shadow:0 2px 8px #000">SentryDeepfake AI</div>
</div>
<script src="https://cdn.jsdelivr.net/npm/three@0.149.0/build/three.min.js"></script>
<script>
const el=document.getElementById('hero');
if(window.THREE){
const W=el.clientWidth,H=250,r=new THREE.WebGLRenderer({antialias:true,alpha:true});
r.setSize(W,H);r.setPixelRatio(window.devicePixelRatio);el.prepend(r.domElement);
r.domElement.style.position='absolute';
const s=new THREE.Scene(),c=new THREE.PerspectiveCamera(45,W/H,0.1,100);c.position.z=6;
const g=new THREE.Group();s.add(g);
g.add(new THREE.Mesh(new THREE.IcosahedronGeometry(1.5,2),
 new THREE.MeshBasicMaterial({color:0x38BDF8,wireframe:true,transparent:true,opacity:.75})));
g.add(new THREE.Mesh(new THREE.TorusGeometry(2.1,0.03,8,80),new THREE.MeshBasicMaterial({color:0x22C55E})));
const ring2=new THREE.Mesh(new THREE.TorusGeometry(2.4,0.02,8,80),new THREE.MeshBasicMaterial({color:0xF87171}));
ring2.rotation.x=Math.PI/2;g.add(ring2);
const n=500,p=new Float32Array(n*3);for(let i=0;i<n*3;i++)p[i]=(Math.random()-.5)*14;
const pg=new THREE.BufferGeometry();pg.setAttribute('position',new THREE.BufferAttribute(p,3));
const pts=new THREE.Points(pg,new THREE.PointsMaterial({color:0x93C5FD,size:0.04}));s.add(pts);
(function a(){requestAnimationFrame(a);g.rotation.y+=0.006;g.rotation.x+=0.002;ring2.rotation.z+=0.01;
 pts.rotation.y-=0.0008;r.render(s,c);})();
}
</script>
"""

CSS_3D = """<style>
.panel{transition:transform .25s, box-shadow .25s;box-shadow:0 8px 20px rgba(15,23,42,.15)!important;border-radius:14px!important}
.panel:hover{transform:perspective(600px) rotateX(4deg) translateY(-6px);box-shadow:0 18px 32px rgba(15,23,42,.28)!important}
.result3d{box-shadow:0 14px 30px rgba(0,0,0,.35), inset 0 2px 0 rgba(255,255,255,.35);
 background-image:linear-gradient(160deg,rgba(255,255,255,.22),rgba(0,0,0,.25))!important;}
</style>"""
