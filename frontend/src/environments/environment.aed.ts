// Single-origin deployment of the AED prototype (docker compose, cloud):
// nginx serves the app and proxies /api, /cms, /media and /flags, exactly like the dev-server proxy.
// "production: false" keeps the portal services on relative URLs instead of api.<host> and cms.<host>.
export const environment = {
  production: false,
  name: 'aed',
  // AED prototype: demo accounts of aed_service (fictional data, see aed_service/README.md), offered on the
  // AED sign-in cards. Deliberately absent from environment.prod.ts and environment.int.ts.
  aedDemoAccounts: [
    { rola: 'firma', opis: 'Sprzedawca AED', email: 'serwis@aed.example', haslo: 'serwis-demo' },
    { rola: 'firma', opis: 'Producent AED', email: 'pulsar@aed.example', haslo: 'pulsar-demo' },
    { rola: 'ministerstwo', opis: 'Ministerstwo', email: 'ministerstwo@aed.example', haslo: 'ministerstwo-demo' },
  ],
};
