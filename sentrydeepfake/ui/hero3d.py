"""Lightweight 3D header: rotating wireframe face inside a shield with scan line with particles (three.js CDN)."""

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
const wire=(geo,col,op)=>new THREE.LineSegments(new THREE.WireframeGeometry(geo),
 new THREE.LineBasicMaterial({color:col,transparent:true,opacity:op}));
// low-poly head
const head=wire(new THREE.IcosahedronGeometry(1,2),0x38BDF8,.85);head.scale.set(.85,1.1,.9);g.add(head);
const jaw=wire(new THREE.ConeGeometry(.55,.6,8,1,true),0x38BDF8,.6);jaw.position.set(0,-.95,.1);jaw.rotation.x=Math.PI;g.add(jaw);
const nose=wire(new THREE.ConeGeometry(.12,.35,4),0x67E8F9,.9);nose.position.set(0,-.05,.85);nose.rotation.x=Math.PI/2;g.add(nose);
[-.32,.32].forEach(x=>{const e=new THREE.Mesh(new THREE.SphereGeometry(.09,8,8),
 new THREE.MeshBasicMaterial({color:0x22D3EE}));e.position.set(x,.2,.72);g.add(e);});
// shield outline around the face
const sh=new THREE.Shape();sh.moveTo(0,1.9);sh.quadraticCurveTo(1.2,1.8,1.7,1.5);
sh.quadraticCurveTo(1.7,-.6,0,-2);sh.quadraticCurveTo(-1.7,-.6,-1.7,1.5);sh.quadraticCurveTo(-1.2,1.8,0,1.9);
const shield=new THREE.Line(new THREE.BufferGeometry().setFromPoints(sh.getPoints(60)),
 new THREE.LineBasicMaterial({color:0x60A5FA}));shield.position.z=-.3;
const shield2=shield.clone();shield2.scale.set(1.08,1.08,1);shield2.material=new THREE.LineBasicMaterial({color:0x22C55E});
s.add(shield);s.add(shield2);
// scanning line
const scan=new THREE.Mesh(new THREE.PlaneGeometry(3.4,.04),new THREE.MeshBasicMaterial({color:0x22D3EE,transparent:true,opacity:.9}));
scan.position.z=1.1;s.add(scan);
const n=300,p=new Float32Array(n*3);for(let i=0;i<n*3;i++)p[i]=(Math.random()-.5)*14;
const pg=new THREE.BufferGeometry();pg.setAttribute('position',new THREE.BufferAttribute(p,3));
const pts=new THREE.Points(pg,new THREE.PointsMaterial({color:0x93C5FD,size:0.035}));s.add(pts);
let t=0;(function a(){requestAnimationFrame(a);t+=0.016;g.rotation.y=Math.sin(t*.5)*0.9;
 scan.position.y=Math.sin(t*1.5)*1.6;pts.rotation.y-=0.0008;r.render(s,c);})();
}
</script>
"""

CSS_3D = """<style>
.panel{transition:transform .25s, box-shadow .25s;box-shadow:0 8px 20px rgba(15,23,42,.15)!important;border-radius:14px!important}
.panel:hover{transform:perspective(600px) rotateX(4deg) translateY(-6px);box-shadow:0 18px 32px rgba(15,23,42,.28)!important}
.result3d{box-shadow:0 14px 30px rgba(0,0,0,.35), inset 0 2px 0 rgba(255,255,255,.35);
 background-image:linear-gradient(160deg,rgba(255,255,255,.22),rgba(0,0,0,.25))!important;}
</style>"""
