import { HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { from, map, Observable, of, throwError } from 'rxjs';

import {
  AedAccepted,
  AedApiService,
  AedCondition,
  AedPage,
  AedProblem,
  AedRecord,
  AedSession,
  AedSignal,
  AedStats,
  AedStatus,
  AedSubmission,
} from './aed-api.service';
import { aedField, aedRequired, AedValue, aedValueError } from './aed-schema';

// MOCK of the AED service (docs/api-aed.md) for work without the backend. Same methods and JSON shapes
// as AedApiService; aed.routes.ts decides which of the two is used. The places below are invented.
// The store is module-level on purpose: the portal pages and the QR screen get separate injectors.

/** Any non-empty token opens the manager view in the mock; use this one in demo links. */
export const AED_MOCK_TOKEN = 'demo';

// Contract: the public scope of a record has no contact data and no serial number.
const NOT_PUBLIC = ['numer_seryjny', 'dysponent_email', 'dysponent_telefon', 'dysponent_regon'];

const today = () => new Date().toISOString().slice(0, 10);

const notFound = () =>
  throwError(
    () =>
      new HttpErrorResponse({
        status: 404,
        error: { blad: { kod: 'brak_urzadzenia', komunikat: 'W rejestrze nie ma urządzenia o tym identyfikatorze.' } },
      }),
  );

const RECORDS: AedRecord[] = [
  {
    id_aed: 'AED-7F3K9Q2M4XTB',
    status: 'zgloszony',
    kompletnosc: 41,
    producent: 'Philips',
    model: 'HeartStart FRx',
    numer_seryjny: 'B21K-04127',
    data_produkcji: '2026-03-01',
    data_waznosci_elektrod: '2028-03-31',
    data_waznosci_baterii: '2030-01-31',
    dysponent_nazwa: 'Szkoła Podstawowa nr 4 w Legionowie',
    dysponent_email: 'sekretariat@sp4.example',
    wprowadzajacy_nazwa: 'MedSprzęt Sp. z o.o.',
    zrodlo: 'zgloszenie',
  },
  {
    id_aed: 'AED-2HX8M5PD9RVC',
    status: 'aktywny',
    kompletnosc: 96,
    nazwa: 'Urząd Miasta Legionowo',
    cecha_ulicy: 'ulica',
    nazwa_ulicy: 'Piłsudskiego',
    nr_budynku: '41',
    miejscowosc: 'Legionowo',
    szerokosc_geograficzna: 52.395198,
    dlugosc_geograficzna: 20.931382,
    opis_lokalizacji: 'Hol główny, przy portierni, na lewo od wejścia',
    dostep: 'publiczny',
    godziny_dostepu: 'Mo-Fr 08:00-16:00',
    producent: 'Philips',
    model: 'HeartStart FRx',
    numer_seryjny: 'B21K-03310',
    dysponent_nazwa: 'Urząd Miasta Legionowo',
    data_weryfikacji: '2026-11-15',
    zrodlo: 'zgloszenie',
  },
  {
    id_aed: 'AED-K4T7W2NB6YQE',
    status: 'aktywny',
    kompletnosc: 88,
    nazwa: 'Dworzec autobusowy w Krośnie',
    cecha_ulicy: 'ulica',
    nazwa_ulicy: 'Kolejowa',
    nr_budynku: '1',
    miejscowosc: 'Krosno',
    szerokosc_geograficzna: 49.69354,
    dlugosc_geograficzna: 21.75582,
    dostep: 'publiczny',
    godziny_dostepu: '24/7',
    producent: 'ZOLL',
    model: 'AED Plus',
    dysponent_nazwa: 'Miejska Komunikacja Samochodowa w Krośnie',
    data_weryfikacji: '2026-10-02',
    zrodlo: 'dane.gov.pl/40593',
  },
  {
    id_aed: 'AED-9PLC3VZ8D1HM',
    status: 'aktywny',
    kompletnosc: 79,
    nazwa: 'Pływalnia miejska w Markach',
    cecha_ulicy: 'ulica',
    nazwa_ulicy: 'Wspólna',
    nr_budynku: '40',
    miejscowosc: 'Marki',
    szerokosc_geograficzna: 52.32405,
    dlugosc_geograficzna: 21.10241,
    dostep: 'ograniczony',
    godziny_dostepu: 'Mo-Su 06:00-22:00',
    dysponent_nazwa: 'Mareckie Centrum Edukacyjno-Rekreacyjne',
    data_weryfikacji: '2026-09-18',
    zrodlo: 'zgloszenie',
  },
  {
    id_aed: 'AED-5QJ1R8FA7GXU',
    status: 'niepotwierdzony',
    kompletnosc: 52,
    nazwa: 'Stacja metra Centrum',
    miejscowosc: 'Warszawa',
    szerokosc_geograficzna: 52.23106,
    dlugosc_geograficzna: 21.01051,
    dostep: 'publiczny',
    zrodlo: 'um.warszawa.pl',
  },
  {
    id_aed: 'AED-W6E2B9TK3NSL',
    status: 'niepotwierdzony',
    kompletnosc: 34,
    nazwa: 'Apteka przy Rynku',
    miejscowosc: 'Przemyśl',
    szerokosc_geograficzna: 49.78213,
    dlugosc_geograficzna: 22.76774,
    zrodlo: 'openstreetmap',
  },
  {
    id_aed: 'AED-M8D4Y1CH5ZPJ',
    status: 'nieaktualny',
    kompletnosc: 71,
    nazwa: 'Hala sportowa przy ulicy Sportowej',
    cecha_ulicy: 'ulica',
    nazwa_ulicy: 'Sportowa',
    nr_budynku: '3',
    miejscowosc: 'Przemyśl',
    szerokosc_geograficzna: 49.77642,
    dlugosc_geograficzna: 22.78015,
    dostep: 'ograniczony',
    godziny_dostepu: 'Mo-Fr 07:00-21:00',
    dysponent_nazwa: 'Przemyski Ośrodek Sportu i Rekreacji',
    data_weryfikacji: '2025-04-30',
    zrodlo: 'dane.gov.pl/2893',
  },
  {
    id_aed: 'AED-T3N9G6XQ2KBW',
    status: 'wycofany',
    kompletnosc: 63,
    nazwa: 'Dawny budynek biblioteki',
    miejscowosc: 'Marki',
    szerokosc_geograficzna: 52.3219,
    dlugosc_geograficzna: 21.1067,
    dysponent_nazwa: 'Urząd Miasta Marki',
    zrodlo: 'zgloszenie',
  },
];

function store(row: Record<string, AedValue>, wprowadzajacy: string): AedAccepted {
  const id_aed = 'AED-' + Math.random().toString(36).slice(2, 14).toUpperCase().padEnd(12, '0');
  RECORDS.unshift({
    ...row,
    id_aed,
    status: 'zgloszony',
    kompletnosc: 40,
    zrodlo: 'zgloszenie',
    wprowadzajacy_nazwa: wprowadzajacy,
  });
  return {
    id_aed,
    producent: String(row['producent']),
    model: String(row['model']),
    numer_seryjny: String(row['numer_seryjny']),
    naklejka_url: '', // the sticker SVG is drawn by the real service only
    link_aktywacyjny: `/aed/qr/${id_aed}?t=${AED_MOCK_TOKEN}`,
  };
}

/** Problems of one row against profile `sprzedaz`: required values, then schema constraints. */
function rowProblems(row: Record<string, AedValue>, wiersz: number): AedProblem[] {
  const required = aedRequired('sprzedaz');
  return Object.keys(row).flatMap((pole) => {
    const field = aedField(pole);
    const empty = String(row[pole] ?? '').trim() === '';
    const komunikat = !field
      ? ''
      : empty
        ? required.includes(pole) && 'Uzupełnij wartość. To pole jest wymagane przy zgłoszeniu sprzedaży.'
        : aedValueError(field, row[pole]);
    return komunikat ? [{ wiersz, pole, poziom: 'blad' as const, kod: 'mock', komunikat }] : [];
  });
}

function submission(
  rows: Record<string, AedValue>[],
  headerProblems: AedProblem[],
  save: string | null,
): AedSubmission {
  const problemy = [...headerProblems];
  const przyjete: AedAccepted[] = [];
  let good = 0;
  let duplikaty = 0;
  rows.forEach((row, index) => {
    const found = rowProblems(row, index + 2);
    problemy.push(...found);
    if (found.length || headerProblems.length) return;
    if (RECORDS.some((r) => r.producent === row['producent'] && r.numer_seryjny === row['numer_seryjny'])) {
      duplikaty++;
      return;
    }
    good++;
    if (save !== null) przyjete.push(store(row, save));
  });
  return {
    id: Date.now(),
    utworzono: new Date().toISOString().slice(0, 19),
    podsumowanie: {
      wiersze: rows.length,
      przyjete: good,
      odrzucone: rows.length - good - duplikaty,
      bledy: problemy.length,
      ostrzezenia: 0,
      duplikaty,
    },
    problemy,
    przyjete,
  };
}

/** CSV text checked against profile `sprzedaz`; `save` is the reporting company, or null for a preview. */
export function aedMockCsv(text: string, save: string | null = null): AedSubmission {
  // ponytail: plain comma split, no quoted cells. The binding check is aed_standard behind POST /zgloszenia.
  const lines = text
    .replace(/^\uFEFF/, '')
    .split(/\r?\n/)
    .filter((line) => line.trim());
  const header = (lines[0] ?? '').split(',').map((cell) => cell.trim());
  const headerProblems: AedProblem[] = aedRequired('sprzedaz')
    .filter((pole) => !header.includes(pole))
    .map((pole) => ({
      wiersz: 1,
      pole,
      poziom: 'blad',
      kod: 'mock',
      komunikat: 'Dodaj tę kolumnę. Jest wymagana przy zgłoszeniu sprzedaży.',
    }));
  const rows = lines.slice(1).map((line) => {
    const cells = line.split(',');
    return Object.fromEntries(header.map((column, position) => [column, (cells[position] ?? '').trim()]));
  });
  return submission(rows, headerProblems, save);
}

@Injectable()
export class AedMockService extends AedApiService {
  override login(email: string): Observable<AedSession> {
    const session: AedSession = {
      token: AED_MOCK_TOKEN,
      konto: { id: 1, nazwa: `Konto demonstracyjne (${email})`, rola: 'firma', typ_podmiotu: 'sprzedawca' },
    };
    this.remember(session);
    return of(session);
  }

  override devices(params: { status?: AedStatus; q?: string }): Observable<AedPage<AedRecord>> {
    const q = (params.q ?? '').toLowerCase();
    const dane = RECORDS.filter(
      (r) =>
        (!params.status || r.status === params.status) &&
        (!q || `${r['nazwa'] ?? ''} ${r['miejscowosc'] ?? ''}`.toLowerCase().includes(q)),
    );
    return of({ dane, razem: dane.length, strona: 1, na_stronie: 50 });
  }

  override stats(): Observable<AedStats> {
    const wg_statusu: AedStats['wg_statusu'] = {};
    RECORDS.forEach((r) => (wg_statusu[r.status] = (wg_statusu[r.status] ?? 0) + 1));
    const srednia_kompletnosc = Math.round(RECORDS.reduce((sum, r) => sum + +r.kompletnosc, 0) / RECORDS.length);
    return of({
      razem: RECORDS.length,
      srednia_kompletnosc,
      wg_statusu,
      wg_zrodla: {},
      dostawcy: 1,
      potwierdzone_90_dni: wg_statusu.aktywny ?? 0,
    });
  }

  override device(id: string, t?: string): Observable<AedRecord> {
    const record = RECORDS.find((r) => r.id_aed === id);
    if (!record) return notFound();
    const visible = Object.entries(record).filter(([column]) => t || !NOT_PUBLIC.includes(column));
    return of(Object.fromEntries(visible) as AedRecord);
  }

  override submitCsv(plik: File, save: boolean): Observable<AedSubmission> {
    return from(plik.text()).pipe(map((text) => aedMockCsv(text, save ? this.account().nazwa : null)));
  }

  override registerDevice(values: Record<string, AedValue>): Observable<AedSubmission> {
    return of(submission([values], [], this.account().nazwa));
  }

  override confirm(
    id: string,
    body: Record<string, AedValue> & { t: string; stan: AedCondition; uwagi?: string },
  ): Observable<AedRecord> {
    const record = RECORDS.find((r) => r.id_aed === id);
    if (!record) return notFound();
    const { t, stan, uwagi, ...values } = body;
    void [t, stan, uwagi];
    Object.assign(record, values, {
      status: 'aktywny',
      data_weryfikacji: today(),
      sposob_weryfikacji: 'qr',
      kompletnosc: 92,
    });
    return of({ ...record });
  }

  override signal(id: string, body: AedSignal): Observable<unknown> {
    return RECORDS.some((r) => r.id_aed === id) ? of(body) : notFound();
  }
}
