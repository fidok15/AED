// Single-origin deployment of the AED prototype (docker compose, cloud):
// nginx serves the app and proxies /api, /cms, /media and /flags, exactly like the dev-server proxy.
// "production: false" keeps the portal services on relative URLs instead of api.<host> and cms.<host>.
export const environment = {
  production: false,
  name: 'aed',
};
