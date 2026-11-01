// Escalado de la escena nativa (1372x764) a la pantalla: "sharp-bilinear".
// 1) escena nativa -> canvas intermedio a escala entera k = ceil(escala), sin suavizado;
// 2) intermedio -> pantalla con suavizado. Píxeles parejos sin columnas de 1 y 2 px alternadas.

export class Scaler {
  constructor(screen, width, height, fit = "cover") {
    this.screen = screen;
    this.w = width;
    this.h = height;
    this.fit = fit;
    this.mid = document.createElement("canvas");
    this.resize();
    addEventListener("resize", () => this.resize());
  }

  resize() {
    const dpr = devicePixelRatio || 1;
    const W = Math.round(innerWidth * dpr), H = Math.round(innerHeight * dpr);
    this.screen.width = W;
    this.screen.height = H;
    const s = this.fit === "contain" ? Math.min(W / this.w, H / this.h) : Math.max(W / this.w, H / this.h);
    this.scale = s;
    this.k = Math.max(1, Math.ceil(s - 1e-6));
    this.mid.width = this.w * this.k;
    this.mid.height = this.h * this.k;
    // Rectángulo de la escena en la pantalla (centrado; con cover se recorta lo que sobra)
    this.dw = this.w * s;
    this.dh = this.h * s;
    this.dx = (W - this.dw) / 2;
    this.dy = (H - this.dh) / 2;
  }

  /** Copia la escena nativa a la pantalla. */
  present(scene, border = "#000") {
    const m = this.mid.getContext("2d");
    m.imageSmoothingEnabled = false;
    m.drawImage(scene, 0, 0, this.mid.width, this.mid.height);
    const c = this.screen.getContext("2d");
    c.fillStyle = border;
    c.fillRect(0, 0, this.screen.width, this.screen.height);
    c.imageSmoothingEnabled = true;
    c.imageSmoothingQuality = "high";
    c.drawImage(this.mid, this.dx, this.dy, this.dw, this.dh);
  }

  /** Punto de la escena nativa -> pantalla (para textos de debug nítidos). */
  toScreen(x, y) {
    return [this.dx + x * this.scale, this.dy + y * this.scale];
  }
}
