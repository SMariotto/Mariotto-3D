// Demo do sistema de rostos no navegador (three.js).
// O que interessa para um jogo esta em setRosto() e tocarAnimacao().
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

const TIPOS = ["Clássico", "Animado", "Focado", "Sardento", "Tranquilo"];
const ANIMS = ["Piscar um olho", "Piscar os dois", "Força", "Dor", "Felicidade"];
const FPS = 10; // quadros do rosto por segundo

const view = document.getElementById("view");
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
view.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1d1f24);
const camera = new THREE.PerspectiveCamera(30, 1, 0.01, 10);
camera.position.set(0, 0.36, 0.42);
const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0.34, 0);
controls.enableDamping = true;
scene.add(new THREE.HemisphereLight(0xffffff, 0x445066, 2.2));
const sun = new THREE.DirectionalLight(0xffffff, 1.6);
sun.position.set(0.4, 1, 1.2);
scene.add(sun);

let rostoMap = null;
let estado = { tipo: 0, anim: 0, quadro: 0 };
let tocando = null;

// ---- o que um jogo precisa ----
function setRosto(tipo, anim, quadro) {
  // atlas: 25 colunas (tipo*5 + quadro) x 5 linhas (animacao)
  estado = { tipo, anim, quadro };
  if (rostoMap) rostoMap.offset.set((tipo * 5 + quadro) / 25, anim / 5);
}
function tocarAnimacao(anim) {
  tocando = { anim, inicio: performance.now() };
}
// --------------------------------

function atualizarAnimacao(agora) {
  if (!tocando) return;
  const q = Math.floor(((agora - tocando.inicio) / 1000) * FPS);
  if (q >= 5) {
    setRosto(estado.tipo, 0, 0);
    tocando = null;
  } else {
    setRosto(estado.tipo, tocando.anim, q);
  }
}

let proximaPiscada = performance.now() + 2500;
function piscarSozinho(agora) {
  if (!document.getElementById("auto").checked || tocando) return;
  if (agora > proximaPiscada) {
    tocarAnimacao(1);
    proximaPiscada = agora + 2200 + Math.random() * 2500;
  }
}

function b64ToBuffer(b64) {
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out.buffer;
}

new GLTFLoader().parse(b64ToBuffer(window.MODEL_GLB_B64), "", (gltf) => {
  scene.add(gltf.scene);
  gltf.scene.traverse((o) => {
    if (o.isMesh && o.name.startsWith("Rosto_Expressao")) {
      rostoMap = o.material.map;
      o.renderOrder = 1;
      o.material.depthWrite = false;
    }
  });
  setRosto(0, 0, 0);
  window.__pronto = true;
});

function montarBotoes(id, nomes, onClick) {
  const box = document.getElementById(id);
  nomes.forEach((n, i) => {
    const b = document.createElement("button");
    b.textContent = n;
    b.onclick = () => onClick(i, b, box);
    box.appendChild(b);
  });
}
montarBotoes("tipos", TIPOS, (i, b, box) => {
  box.querySelectorAll("button").forEach((x) => x.classList.remove("on"));
  b.classList.add("on");
  setRosto(i, tocando ? estado.anim : 0, tocando ? estado.quadro : 0);
});
document.querySelector("#tipos button").classList.add("on");
montarBotoes("anims", ANIMS, (i) => tocarAnimacao(i));

function resize() {
  const w = view.clientWidth, h = view.clientHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
window.addEventListener("resize", resize);
resize();

window.__setRosto = setRosto;
renderer.setAnimationLoop((t) => {
  const agora = performance.now();
  piscarSozinho(agora);
  atualizarAnimacao(agora);
  controls.update();
  renderer.render(scene, camera);
});
