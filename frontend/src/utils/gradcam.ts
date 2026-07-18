/** Mock Grad-CAM 热力图（后续接入真实 CAM 权重） */

export function generateGradCamBase64(): string {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" preserveAspectRatio="none">
    <defs>
      <radialGradient id="h1" cx="40%" cy="35%" r="35%">
        <stop offset="0%" stop-color="rgba(255,0,0,0.85)"/>
        <stop offset="50%" stop-color="rgba(255,165,0,0.55)"/>
        <stop offset="100%" stop-color="rgba(255,255,0,0.05)"/>
      </radialGradient>
      <radialGradient id="h2" cx="65%" cy="55%" r="25%">
        <stop offset="0%" stop-color="rgba(255,100,0,0.7)"/>
        <stop offset="100%" stop-color="rgba(255,255,0,0.05)"/>
      </radialGradient>
    </defs>
    <rect width="100" height="100" fill="url(#h1)"/>
    <rect width="100" height="100" fill="url(#h2)"/>
  </svg>`;
  return btoa(unescape(encodeURIComponent(svg)));
}

export function gradCamOverlayUrl(): string {
  return `data:image/svg+xml;base64,${generateGradCamBase64()}`;
}
