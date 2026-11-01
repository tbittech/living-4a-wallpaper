// Carga el bundle de un tema (lo genera wallpaper/export_bundle.py): bundle.json y todas sus imágenes.

import { prepare } from "./layers.js";

function image(src) {
  return new Promise((ok, fail) => {
    const img = new Image();
    img.onload = () => ok(img);
    img.onerror = () => fail(new Error(`No se pudo cargar ${src}`));
    img.src = src;
  });
}

export async function loadBundle(theme) {
  const base = `bundle/${theme}/`;
  const res = await fetch(base + "bundle.json");
  if (!res.ok) throw new Error(`Falta ${base}bundle.json: correr python -I wallpaper/export_bundle.py`);
  const b = await res.json();
  const jobs = [];
  b.bg = {};
  for (const bg of b.backgrounds) jobs.push(image(`${base}bg/${bg}.png`).then((img) => (b.bg[bg] = img)));
  for (const l of b.layers) {
    l.imgs = {};
    for (const bg of b.backgrounds) {
      jobs.push(image(`${base}layers/${bg}/${l.name}.png`).then((img) => (l.imgs[bg] = img)));
    }
  }
  for (const c of Object.values(b.characters)) jobs.push(image(base + c.atlas).then((img) => (c.img = img)));
  await Promise.all(jobs);
  prepare(b.layers);
  return b;
}
