const CARD_TAG = "tank-utility-ng-gauge";
const ASSET_BASE = "/tank_utility_ng/frontend/tanks";

const TANKS = {
  horizontal: [
    { capacity: 250, file: "propane-250gal.svg", regions: [{ x: 8, y: 21, w: 48, h: 22, rx: 11, ry: 11 }] },
    { capacity: 320, file: "propane-320gal.svg", regions: [{ x: 7, y: 21, w: 50, h: 22, rx: 11, ry: 11 }] },
    { capacity: 500, file: "propane-500gal.svg", regions: [{ x: 5, y: 20, w: 54, h: 24, rx: 12, ry: 12 }] },
    { capacity: 1000, file: "propane-1000gal.svg", regions: [{ x: 4, y: 19, w: 56, h: 26, rx: 13, ry: 13 }] },
    { capacity: 1500, file: "propane-1500gal.svg", regions: [{ x: 3, y: 18, w: 58, h: 28, rx: 14, ry: 14 }] },
    { capacity: 2000, file: "propane-2000gal.svg", regions: [{ x: 2, y: 17, w: 60, h: 30, rx: 15, ry: 15 }] },
    { capacity: 4000, file: "propane-4000gal.svg", regions: [{ x: 1, y: 16, w: 62, h: 32, rx: 16, ry: 16 }] },
  ],
  vertical: [
    { capacity: 50, file: "propane-50gal.svg", regions: [{ x: 18, y: 16, w: 28, h: 38, rx: 12, ry: 12 }] },
    { capacity: 120, file: "propane-120gal.svg", regions: [{ x: 18, y: 16, w: 28, h: 38, rx: 12, ry: 12 }] },
    { capacity: 240, file: "propane-240gal-2x120.svg", regions: [{ x: 18, y: 26, w: 12, h: 28, rx: 6, ry: 6 }, { x: 34, y: 26, w: 12, h: 28, rx: 6, ry: 6 }] },
    { capacity: 360, file: "propane-360gal-3x120.svg", regions: [{ x: 10, y: 26, w: 12, h: 28, rx: 6, ry: 6 }, { x: 26, y: 26, w: 12, h: 28, rx: 6, ry: 6 }, { x: 42, y: 26, w: 12, h: 28, rx: 6, ry: 6 }] },
    { capacity: 480, file: "propane-480gal-4x120.svg", regions: [{ x: 2, y: 26, w: 12, h: 28, rx: 6, ry: 6 }, { x: 18, y: 26, w: 12, h: 28, rx: 6, ry: 6 }, { x: 34, y: 26, w: 12, h: 28, rx: 6, ry: 6 }, { x: 50, y: 26, w: 12, h: 28, rx: 6, ry: 6 }] },
  ],
};

class TankUtilityNGGauge extends HTMLElement {
  setConfig(config) {
    if (!config) throw new Error("Invalid configuration");
    for (const key of ["tank_level", "gallons_remaining", "tank_capacity"]) {
      if (!config[key]) throw new Error(`Missing required config key: ${key}`);
    }
    this._config = config;
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
      const style = document.createElement("style");
      style.textContent = `
        ha-card { overflow: hidden; }
        .wrap { position: relative; width: 100%; aspect-ratio: 1 / 1; }
        .tank { width: 100%; height: 100%; display: block; }
        .label { position: absolute; left: 50%; transform: translateX(-50%); color: white; text-shadow: 0 0 5px rgba(0,0,0,.85); font-family: var(--ha-card-header-font-family, system-ui, sans-serif); text-align: center; pointer-events: none; user-select: none; }
        .level { top: 15%; font-size: 28px; font-weight: 800; line-height: 1; }
        .gallons { top: 23%; font-size: 15px; font-weight: 600; }
      `;
      this.shadowRoot.appendChild(style);
      this._root = document.createElement("div");
      this.shadowRoot.appendChild(this._root);
    }
  }

  set hass(hass) { this._hass = hass; this._render(); }
  getCardSize() { return 4; }

  static getStubConfig() {
    return {
      tank_level: "sensor.house_tank_tank_level",
      gallons_remaining: "sensor.house_tank_gallons_remaining",
      tank_capacity: "sensor.house_tank_tank_capacity",
      delivery: "binary_sensor.house_tank_delivery_detected",
    };
  }

  _state(id) { return id ? this._hass?.states?.[id] : undefined; }
  _str(id, fallback = "") { return this._state(id)?.state ?? fallback; }
  _num(id, fallback = 0) { const value = Number(this._str(id, fallback)); return Number.isFinite(value) ? value : fallback; }

  _orientation() {
    if (this._config.orientation) {
      const orientationEntity = this._state(this._config.orientation);
      if (orientationEntity) return String(orientationEntity.state).toLowerCase();
    }
    return String(this._state(this._config.tank_capacity)?.attributes?.orientation ?? "horizontal").toLowerCase();
  }

  _closestTank(capacity, orientation) {
    const set = TANKS[orientation] ?? TANKS.horizontal;
    return set.reduce((best, candidate) => Math.abs(candidate.capacity - capacity) < Math.abs(best.capacity - capacity) ? candidate : best);
  }

  _fillColor(percent) {
    const red = this._config.red_threshold ?? 25;
    const amber = this._config.amber_threshold ?? 50;
    if (percent <= red) return this._config.red_color ?? "#d32f2f";
    if (percent <= amber) return this._config.amber_color ?? "#f9a825";
    return this._config.green_color ?? "#2e7d32";
  }

  _deliveryFlashActive() {
    const entity = this._state(this._config.delivery);
    if (!entity) return false;
    const detectedAt = entity.attributes?.detected_at ?? (entity.state === "on" ? entity.last_changed : null);
    if (!detectedAt) return false;
    const changed = new Date(detectedAt).getTime();
    return Number.isFinite(changed) && (Date.now() - changed) >= 0 && (Date.now() - changed) < 24 * 60 * 60 * 1000;
  }

  _render() {
    if (!this._hass || !this._config || !this._root) return;
    const percent = Math.max(0, Math.min(100, this._num(this._config.tank_level, 0)));
    const capacity = this._num(this._config.tank_capacity, 0);
    const orientation = this._orientation() === "vertical" ? "vertical" : "horizontal";
    const tank = this._closestTank(capacity, orientation);
    const imageUrl = `${ASSET_BASE}/${orientation}/${tank.file}`;
    const color = this._fillColor(percent);
    const regionTop = Math.min(...tank.regions.map((r) => r.y));
    const regionBottom = Math.max(...tank.regions.map((r) => r.y + r.h));
    const regionLeft = Math.min(...tank.regions.map((r) => r.x));
    const regionRight = Math.max(...tank.regions.map((r) => r.x + r.w));
    const fillY = regionBottom - ((percent / 100) * (regionBottom - regionTop));
    const clipRects = tank.regions.map((r) => `<rect x="${r.x}" y="${r.y}" width="${r.w}" height="${r.h}" rx="${r.rx}" ry="${r.ry}"/>`).join("");
    const delivery = this._deliveryFlashActive() ? `<g><rect x="1.5" y="1.5" width="61" height="61" rx="4" fill="none" stroke="#00e676" stroke-width="1.5" opacity="0"><animate attributeName="opacity" values="0;0.95;0" dur="1.2s" repeatCount="indefinite"/></rect><text x="32" y="6.5" text-anchor="middle" font-size="3.4" font-family="sans-serif" font-weight="700" fill="#00e676" opacity="0">DELIVERY<animate attributeName="opacity" values="0;1;0" dur="1.2s" repeatCount="indefinite"/></text></g>` : "";
    const gallonsState = this._state(this._config.gallons_remaining);
    const gallons = gallonsState ? `${gallonsState.state}${gallonsState.attributes?.unit_of_measurement ? ` ${gallonsState.attributes.unit_of_measurement}` : ""}` : "—";
    this._root.innerHTML = `<ha-card><div class="wrap"><svg class="tank" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" preserveAspectRatio="xMidYMid meet"><defs><clipPath id="tank-fill">${clipRects}</clipPath></defs><g clip-path="url(#tank-fill)"><rect x="${regionLeft}" y="${fillY}" width="${regionRight - regionLeft}" height="${regionBottom - fillY}" fill="${color}" opacity="0.55"/><rect x="${regionLeft}" y="${fillY}" width="${regionRight - regionLeft}" height="0.45" fill="white" opacity="0.35"/></g><image href="${imageUrl}" x="0" y="0" width="64" height="64" preserveAspectRatio="xMidYMid meet"/>${delivery}</svg><div class="label level">${percent.toFixed(0)}%</div><div class="label gallons">${gallons}</div></div></ha-card>`;
  }
}

customElements.define(CARD_TAG, TankUtilityNGGauge);
window.customCards = window.customCards || [];
window.customCards.push({ type: CARD_TAG, name: "Tank Utility NG Gauge", description: "Included Tank Utility NG propane gauge with capacity/orientation-aware artwork, fill level, and delivery indication." });
