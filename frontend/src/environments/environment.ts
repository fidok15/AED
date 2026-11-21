export const environment = {
  production: false,
  name: 'local',
  // AED prototype: demo accounts of aed_service (fictional data, see aed_service/README.md), offered on the
  // AED sign-in cards. Deliberately absent from environment.prod.ts and environment.int.ts.
  aedDemoAccounts: [
    { rola: 'firma', opis: 'Sprzedawca AED', email: 'serwis@aed.example', haslo: 'serwis-demo' },
    { rola: 'firma', opis: 'Producent AED', email: 'pulsar@aed.example', haslo: 'pulsar-demo' },
    { rola: 'ministerstwo', opis: 'Ministerstwo', email: 'ministerstwo@aed.example', haslo: 'ministerstwo-demo' },
  ],
};
