import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable, signal } from '@angular/core';
import { Router, UrlTree } from '@angular/router';
import { LocalizeRouterService } from '@gilsdav/ngx-translate-router';
import { map, Observable, tap } from 'rxjs';

import { AedValue } from './aed-schema';

// Client of the AED service. Paths, field names and JSON shapes follow docs/api-aed.md one to one.
// The mock (aed-mock.service.ts) extends this class; aed.routes.ts picks one of the two.

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

@Injectable()
export class AedApiService {
  private readonly http = inject(HttpClient);
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

  protected remember(session: AedSession | null): void {
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
