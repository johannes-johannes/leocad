import * as THREE from 'https://unpkg.com/three@0.164.0/build/three.module.js';
import { OrbitControls } from 'https://unpkg.com/three@0.164.0/examples/jsm/controls/OrbitControls.js';
import { LDrawLoader } from 'https://unpkg.com/three@0.164.0/examples/jsm/loaders/LDrawLoader.js';

const canvas = document.getElementById('viewer');
const partSelect = document.getElementById('part-select');
const statusEl = document.getElementById('status');
const messageEl = document.getElementById('message');

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
resizeRenderer();

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xf3f4f6);

const camera = new THREE.PerspectiveCamera(45, canvas.clientWidth / canvas.clientHeight, 1, 5000);
camera.position.set(200, 160, 200);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;

scene.add(new THREE.AmbientLight(0xffffff, 0.7));
const sun = new THREE.DirectionalLight(0xffffff, 0.8);
sun.position.set(200, 400, 250);
scene.add(sun);

const loader = new LDrawLoader();
loader.setPath('ldraw/');
loader.setResourcePath('ldraw/');
loader.materials.setPath('ldraw/');
loader.convertCylinders = true;
loader.separateObjects = false;

let currentObject = null;
let animationFrame = null;

init();

async function init() {
  try {
    const response = await fetch('parts_index.json');
    if (!response.ok) {
      throw new Error(`Failed to load parts index: ${response.statusText}`);
    }
    const parts = await response.json();
    populateDropdown(parts);
    if (parts.length > 0) {
      loadPart(parts[0].id);
    } else {
      setMessage('No part files found.');
    }
  } catch (error) {
    console.error(error);
    setMessage('Unable to load parts index. Check the server output for details.');
  }
}

function populateDropdown(parts) {
  partSelect.innerHTML = '';
  for (const part of parts) {
    const option = document.createElement('option');
    option.value = part.id;
    option.textContent = `${part.id} — ${part.name}`;
    partSelect.appendChild(option);
  }

  partSelect.addEventListener('change', () => {
    loadPart(partSelect.value);
  });
}

function loadPart(partId) {
  if (!partId) {
    return;
  }
  setStatus(`Loading ${partId}…`);

  loader.load(
    `parts/${partId}`,
    (group) => {
      setStatus('');
      setMessage('');
      if (currentObject) {
        scene.remove(currentObject);
      }
      currentObject = group;
      group.rotation.x = Math.PI; // align LDraw Y-up to Three.js Z-up
      scene.add(group);
      frameScene(group);
      startAnimationLoop();
    },
    undefined,
    (error) => {
      console.error(error);
      setStatus('');
      setMessage(`Failed to load ${partId}`);
    }
  );
}

function frameScene(object) {
  const box = new THREE.Box3().setFromObject(object);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());

  controls.target.copy(center);

  const maxSize = Math.max(size.x, size.y, size.z);
  const distance = maxSize * 2.5 + 10;
  const direction = new THREE.Vector3(1, 1, 1).normalize();

  camera.position.copy(center).addScaledVector(direction, distance);
  camera.near = Math.max(0.1, distance / 100);
  camera.far = distance * 10;
  camera.updateProjectionMatrix();
}

function startAnimationLoop() {
  if (animationFrame !== null) {
    cancelAnimationFrame(animationFrame);
  }

  function render() {
    animationFrame = requestAnimationFrame(render);
    controls.update();
    renderer.render(scene, camera);
  }

  render();
}

function setStatus(text) {
  if (text) {
    statusEl.textContent = text;
    statusEl.hidden = false;
  } else {
    statusEl.hidden = true;
  }
}

function setMessage(text) {
  messageEl.textContent = text;
}

window.addEventListener('resize', () => {
  resizeRenderer();
  camera.aspect = canvas.clientWidth / canvas.clientHeight;
  camera.updateProjectionMatrix();
});

function resizeRenderer() {
  const { clientWidth, clientHeight } = canvas;
  renderer.setSize(clientWidth, clientHeight, false);
}
