import { HttpBackend, HttpClient, HttpErrorResponse } from '@angular/common/http';
import { afterNextRender, ElementRef, inject, Injectable, Injector, signal } from '@angular/core';
import { Router, UrlTree } from '@angular/router';
import { LocalizeRouterService } from '@gilsdav/ngx-translate-router';
import { map, Observable, tap } from 'rxjs';

import { AedValue } from './aed-schema';

// Client of the AED service. Paths, field names and JSON shapes follow docs/api-aed.md one to one.

const API = '/api/aed';
const SESSION_KEY = 'aed_sesja';

export type AedStatus = 'zgloszony' | 'aktywny' | 'niepotwierdzony' | 'nieaktualny' | 'wycofany';

/** A device: columns of aed_standard/schema.json. The service sends every value as text. */
export interface AedRecord {
  id_aed: string;
  status: AedStatus;
  kompletnosc: number | string;
  [column: string]: AedValue | undefined;
}

export interface AedPage<T> {
  dane: T[];
  razem: number;
  strona: number;
  na_stronie: number;
}

export interface AedStats {
  razem: number;
  srednia_kompletnosc: number;
  wg_statusu: Partial<Record<AedStatus, number>>;
  wg_zrodla: Record<string, number>;
  dostawcy: number;
  potwierdzone_90_dni: number;
  /** ISO time of the last run of each cyclic job; null when it has not run yet. */
  ostatnie_uruchomienia?: { mapper: string | null; przypomnienia: string | null };
}

export interface AedAccount {
  id: number;
  nazwa: string;
  rola: 'firma' | 'ministerstwo';
  typ_podmiotu: string;
}

export interface AedSession {
  token: string;
  konto: AedAccount;
}

export interface AedProblem {
  wiersz: number;
  pole: string;
  poziom: 'blad' | 'ostrzezenie';
  kod: string;
  komunikat: string;
}

export interface AedAccepted {
  id_aed: string;
  producent: string;
  model: string;
  numer_seryjny: string;
  naklejka_url: string;
  link_aktywacyjny: string;
}

export interface AedSubmission {
  id: number;
  utworzono: string;
  podsumowanie: {
    wiersze: number;
    przyjete: number;
    odrzucone: number;
    bledy: number;
    ostrzezenia: number;
    duplikaty: number;
  };
  problemy: AedProblem[];
  /** Empty on a dry run (`sucha_proba`); the count is then only in `podsumowanie.przyjete`. */
  przyjete: AedAccepted[];
  sucha_proba?: boolean;
}

export interface AedDuplicate {
  id: number;
  rekord_a: AedRecord;
  rekord_b: AedRecord;
  odleglosc_m: number;
  podobienstwo: number;
}

/** A message queued for a device owner; the prototype shows the outbox instead of sending e-mail. */
export interface AedMessage {
  id: number;
  rodzaj: string;
  id_aed: string;
  odbiorca: string;
  temat: string;
  tresc: string;
  /** Manager link; null for a message made from a bystander's signal. */
  link: string | null;
  data: string;
}

export interface AedRemindersRun {
  nieaktualne: number;
  prosby_o_potwierdzenie: number;
  przypomnienia_terminow: number;
}

export interface AedMapperRun {
  dodano: number;
  zmieniono: number;
  polaczono: number;
  do_przegladu: number;
}

/** One run of the cyclic jobs (GET /zadania): by the schedule or started from the ministry panel. */
export interface AedJobRun {
  id: number;
  start: string;
  koniec: string | null;
  wyzwalacz: 'harmonogram' | 'ministerstwo';
  rodzaj: 'cykl' | 'mapper' | 'przypomnienia';
  odswiezono: string | null;
  mapper: AedMapperRun | null;
  przypomnienia: AedRemindersRun | null;
  bledy: string[];
}

/** Point of /urzadzenia.geojson. */
export interface AedMapFeature {
  geometry: { coordinates: [number, number] };
  properties: {
    id_aed: string;
    nazwa: string;
    status: AedStatus;
    dostep: string;
    godziny_dostepu: string;
    kompletnosc: number;
    zrodlo: string;
  };
}

/** Row of the company ranking (GET /sprzedawcy). */
export interface AedSeller {
  nazwa: string;
  typ_podmiotu: string;
  miejscowosc: string;
  szerokosc_geograficzna: number;
  dlugosc_geograficzna: number;
  liczba_urzadzen: number;
  srednia_kompletnosc: number;
  /** 0–1 */
  udzial_aktywnych: number;
  odznaka: 'tak' | 'nie';
}

export interface AedSellers {
  dane: AedSeller[];
  /** Badge thresholds: minimum average completeness (0–100) and minimum share of active devices (0–1). */
  progi: { srednia_kompletnosc: number; udzial_aktywnych: number };
}

export type AedCondition = 'sprawny' | 'problem';
export type AedSignalType = 'jest' | 'brak' | 'uszkodzony' | 'zamkniety';

export interface AedSignal {
  typ: AedSignalType;
  szerokosc_geograficzna?: number;
  dlugosc_geograficzna?: number;
  uwagi?: string;
}

/**
 * Message from the error body `{"blad": {"kod", "komunikat", "problemy"}}` (problems come with HTTP 422),
 * with a fallback for network failures.
 */
export function aedErrorMessage(error: HttpErrorResponse): string {
  const blad = error?.error?.blad;
  if (!blad) return 'Nie udało się połączyć z rejestrem. Spróbuj ponownie za chwilę.';
  const problems: AedProblem[] = blad.problemy ?? [];
  return [blad.komunikat, ...problems.map((problem) => `${problem.pole}: ${problem.komunikat}`)].join(' ');
}

/**
 * Turns a contract link such as `/aed/qr/{id_aed}?t=...` into an in-app link with the language prefix.
 * Call in an injection context (a field initialiser).
 */
export function aedLinkFactory(): (link: string) => UrlTree {
  const router = inject(Router);
  const localize = inject(LocalizeRouterService);
  return (link) => {
    const [path, query] = link.split('?');
    // '!' tells the localize router to keep a path segment as it is
    const localized = localize.translateRoute(path.replace(/\//g, '/!')) as string;
    return router.parseUrl(query ? `${localized}?${query}` : localized);
  };
}

/**
 * Moves keyboard focus to an element of the calling component once the view has changed, e.g. to the
 * heading of a result that replaced a form (otherwise focus falls back to the top of the page).
 * Call in an injection context (a field initialiser).
 */
export function aedFocusFactory(): (selector: string) => void {
  const injector = inject(Injector);
  const host = inject<ElementRef<HTMLElement>>(ElementRef);
  return (selector) =>
    afterNextRender(() => host.nativeElement.querySelector<HTMLElement>(selector)?.focus(), { injector });
}

@Injectable()
export class AedApiService {
  // Own client without the portal interceptors: an AED 401 must not end the portal session,
  // and AED answers must not come from the portal's GET cache.
  private readonly http = new HttpClient(inject(HttpBackend));
  private session: AedSession | null = JSON.parse(sessionStorage.getItem(SESSION_KEY) ?? 'null');

  /** Logged-in company or ministry account; null for anonymous visitors. */
  readonly account = signal<AedAccount | null>(this.session?.konto ?? null);

  // POST /sesja
  login(email: string, haslo: string): Observable<AedSession> {
    return this.http.post<AedSession>(`${API}/sesja`, { email, haslo }).pipe(tap((session) => this.remember(session)));
  }

  logout(): void {
    this.remember(null);
  }

  // GET /urzadzenia
  devices(params: {
    status?: AedStatus;
    q?: string;
    strona?: number;
    na_stronie?: number;
  }): Observable<AedPage<AedRecord>> {
    const set = Object.fromEntries(Object.entries(params).filter(([, value]) => value != null && value !== ''));
    return this.http.get<AedPage<AedRecord>>(`${API}/urzadzenia`, { params: set });
  }

  // GET /statystyki
  stats(): Observable<AedStats> {
    return this.http.get<AedStats>(`${API}/statystyki`);
  }

  // GET /urzadzenia/{id_aed}[?t=<token>]: public scope without the token, full record with it
  device(id: string, t?: string): Observable<AedRecord> {
    return this.http.get<AedRecord>(`${API}/urzadzenia/${encodeURIComponent(id)}`, { params: t ? { t } : {} });
  }

  // POST /zgloszenia/sprawdz (preview) and POST /zgloszenia (save); multipart field `plik`
  submitCsv(plik: File, save: boolean): Observable<AedSubmission> {
    const body = new FormData();
    body.append('plik', plik);
    return this.http.post<AedSubmission>(`${API}/zgloszenia${save ? '' : '/sprawdz'}`, body, this.auth());
  }

  // POST /urzadzenia: answers with the same shape as a CSV submission
  registerDevice(values: Record<string, AedValue>): Observable<AedSubmission> {
    return this.http.post<AedSubmission>(`${API}/urzadzenia`, values, this.auth());
  }

  // POST /urzadzenia/{id_aed}/potwierdzenie: the answer carries the full updated record under `rekord`
  confirm(
    id: string,
    body: Record<string, AedValue> & { t: string; stan: AedCondition; uwagi?: string },
  ): Observable<AedRecord> {
    return this.http
      .post<{ rekord: AedRecord }>(`${API}/urzadzenia/${encodeURIComponent(id)}/potwierdzenie`, body)
      .pipe(map((answer) => answer.rekord));
  }

  // POST /urzadzenia/{id_aed}/sygnal
  signal(id: string, body: AedSignal): Observable<unknown> {
    return this.http.post(`${API}/urzadzenia/${encodeURIComponent(id)}/sygnal`, body);
  }

  // GET /urzadzenia.geojson?bbox=minLon,minLat,maxLon,maxLat
  mapPoints(bbox: string): Observable<AedMapFeature[]> {
    return this.http
      .get<{ features: AedMapFeature[] }>(`${API}/urzadzenia.geojson`, { params: { bbox } })
      .pipe(map((collection) => collection.features));
  }

  // GET /sprzedawcy
  sellers(): Observable<AedSellers> {
    return this.http.get<AedSellers>(`${API}/sprzedawcy`);
  }

  // GET /zgloszenia: submissions of the signed-in company, newest first
  submissions(): Observable<AedSubmission[]> {
    return this.http.get<{ dane: AedSubmission[] }>(`${API}/zgloszenia`, this.auth()).pipe(map((page) => page.dane));
  }

  // ---- ministry panel

  /** GET /eksport/dane-gov-pl.csv: public, so a plain link is enough. */
  readonly exportUrl = `${API}/eksport/dane-gov-pl.csv`;

  // GET /duplikaty
  duplicates(): Observable<{ dane: AedDuplicate[]; razem: number }> {
    return this.http.get<{ dane: AedDuplicate[]; razem: number }>(`${API}/duplikaty`, this.auth());
  }

  // POST /duplikaty/{id}: `polacz` keeps record A and withdraws record B
  decideDuplicate(id: number, decyzja: 'polacz' | 'rozdziel'): Observable<unknown> {
    return this.http.post(`${API}/duplikaty/${id}`, { decyzja }, this.auth());
  }

  // GET /wiadomosci
  messages(): Observable<{ dane: AedMessage[]; razem: number }> {
    return this.http.get<{ dane: AedMessage[]; razem: number }>(`${API}/wiadomosci`, this.auth());
  }

  // GET /zadania: last runs of the cyclic jobs, newest first
  jobs(): Observable<AedJobRun[]> {
    return this.http.get<{ dane: AedJobRun[] }>(`${API}/zadania`, this.auth()).pipe(map((page) => page.dane));
  }

  // POST /przypomnienia/uruchom
  runReminders(): Observable<AedRemindersRun> {
    return this.http.post<AedRemindersRun>(`${API}/przypomnienia/uruchom`, {}, this.auth());
  }

  // POST /mapper/uruchom
  runMapper(): Observable<AedMapperRun> {
    return this.http.post<AedMapperRun>(`${API}/mapper/uruchom`, {}, this.auth());
  }

  private remember(session: AedSession | null): void {
    this.session = session;
    this.account.set(session?.konto ?? null);
    // Prototype: the bearer token lives in sessionStorage; move to an HttpOnly cookie with the portal login.
    if (session) sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
    else sessionStorage.removeItem(SESSION_KEY);
  }

  private auth() {
    return { headers: { Authorization: `Bearer ${this.session?.token ?? ''}` } };
  }
}
