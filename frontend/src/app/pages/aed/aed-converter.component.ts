import { HttpBackend, HttpClient } from '@angular/common/http';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { Subscription } from 'rxjs';

import { SeoService } from '@app/services/seo.service';
import { aedErrorMessage, aedFileTooLarge, aedFocusFactory, AedProblem } from './aed-api.service';
import { aedField } from './aed-schema';

// Public converter of a provider's own file to the AED standard (docs/api-aed.md, "Konwerter do standardu").
// Nothing is stored by the service; the provider downloads the result and publishes it on dane.gov.pl.

const API = '/api/aed/konwerter';
/** Values the provider may set once for the whole file (they fill only empty cells). */
const CONSTANTS = ['miejscowosc', 'dostep', 'godziny_dostepu'];

export interface AedConverterColumn {
  kolumna: string;
  przyklady: string[];
  pole: string;
  powod: string;
}

export interface AedConverterAnalysis {
  plik: string;
  format: 'csv' | 'xlsx' | 'geojson';
  kodowanie: string;
  separator: string | null;
  wiersze: number;
  kolumny: AedConverterColumn[];
  pola: { pole: string; tytul: string }[];
  pola_stale: { pole: string; tytul: string; wartosci: string[] | null }[];
  uwagi: string[];
  ostrzezenia: string[];
}

/** One column whose values were rewritten to the standard's spelling (e.g. „Publiczny” → „publiczny”). */
export interface AedConverterNormalization {
  kolumna: string;
  pole: string;
  liczba: number;
  z: string;
  na: string;
  komunikat: string;
}

export interface AedConverterResult {
  nazwa_pliku: string;
  plik_csv: string;
  raport: {
    status: 'przyjety' | 'czesciowo' | 'odrzucony';
    wiersze: number;
    poprawne: number;
    odrzucone: number;
    poza_wykazem_krajowym: number;
    kompletnosc_srednia: number;
    problemy: AedProblem[];
    problemy_razem: number;
    poprawki: string[];
    normalizacje: AedConverterNormalization[];
    /** Fields emptied in the public file (contact, serial number) and the message saying so. */
    ukryte_pola: string[];
    ukryte_komunikat: string;
  };
}

/** Converter: upload any AED file, confirm the column mapping, download a list in the standard. */
@Component({
  selector: 'app-aed-converter',
  standalone: true,
  templateUrl: './aed-converter.component.html',
})
export class AedConverterComponent implements OnInit {
  // Own client without the portal interceptors, as in AedApiService.
  private readonly http = new HttpClient(inject(HttpBackend));
  private readonly seo = inject(SeoService);
  private readonly focus = aedFocusFactory();
  /** Request in flight; a new file cancels it, so a late answer for the previous file never lands. */
  private pending?: Subscription;

  protected readonly file = signal<File | null>(null);
  protected readonly analysis = signal<AedConverterAnalysis | null>(null);
  /** column -> target field ('' = column skipped); starts as the service's proposal. */
  protected readonly mapping = signal<Record<string, string>>({});
  protected readonly constants = signal<Record<string, string>>({});
  protected readonly result = signal<AedConverterResult | null>(null);
  protected readonly busy = signal(false);
  protected readonly error = signal('');

  protected readonly constantFields = computed(() =>
    (this.analysis()?.pola_stale ?? []).filter((field) => CONSTANTS.includes(field.pole)),
  );
  /** Targets chosen for more than one column; the service would reject the mapping. */
  protected readonly repeated = computed(() => {
    const used = Object.values(this.mapping()).filter(Boolean);
    return [...new Set(used.filter((target, i) => used.indexOf(target) !== i))];
  });
  protected readonly downloadHref = computed(() => {
    const result = this.result();
    return result ? 'data:text/csv;charset=utf-8,' + encodeURIComponent(result.plik_csv) : '';
  });
  protected readonly title = (name: string | null) => (name ? (aedField(name)?.title ?? name) : 'Cały plik');
  protected readonly targetTitle = (name: string) =>
    this.analysis()?.pola.find((field) => field.pole === name)?.tytul ?? name;
  protected readonly number = (value: number) => value.toLocaleString('pl-PL');
  protected readonly formatName = (format: AedConverterAnalysis['format']) =>
    ({ csv: 'CSV', xlsx: 'XLSX', geojson: 'GeoJSON' })[format];

  ngOnInit(): void {
    this.seo.setPageTitle(['Konwerter do standardu AED', 'Rejestr AED']);
  }

  protected choose(input: HTMLInputElement): void {
    this.file.set(input.files?.[0] ?? null);
    this.analysis.set(null);
    this.result.set(null);
    this.error.set('');
    this.pending?.unsubscribe();
    this.busy.set(false);
    const file = this.file();
    if (!file) return;
    if (aedFileTooLarge(file)) return this.error.set(aedFileTooLarge(file));
    this.busy.set(true);
    this.pending = this.http.post<AedConverterAnalysis>(`${API}/analiza`, this.form(file)).subscribe({
      next: (analysis) => {
        this.analysis.set(analysis);
        this.mapping.set(Object.fromEntries(analysis.kolumny.map((column) => [column.kolumna, column.pole])));
        this.constants.set({});
        this.busy.set(false);
        this.focus('#aed-conv-mapping');
      },
      error: (error) => {
        this.error.set(aedErrorMessage(error));
        this.busy.set(false);
      },
    });
  }

  protected setTarget(column: string, target: string): void {
    this.mapping.update((mapping) => ({ ...mapping, [column]: target }));
    this.result.set(null);
  }

  protected setConstant(field: string, value: string): void {
    this.constants.update((constants) => ({ ...constants, [field]: value }));
    this.result.set(null);
  }

  protected convert(): void {
    const file = this.file();
    if (!file || this.busy()) return;
    if (this.repeated().length) {
      this.error.set(
        'Każde pole standardu może mieć tylko jedną kolumnę. Popraw wybór dla: ' +
          this.repeated().map(this.targetTitle).join(', ') +
          '.',
      );
      this.focus('#aed-conv-error');
      return;
    }
    this.busy.set(true);
    const body = this.form(file);
    body.append('mapowanie', JSON.stringify(this.mapping()));
    body.append('stale', JSON.stringify(this.constants()));
    this.pending = this.http.post<AedConverterResult>(`${API}/konwersja`, body).subscribe({
      next: (result) => {
        this.result.set(result);
        this.error.set('');
        this.busy.set(false);
        this.focus('#aed-conv-result');
      },
      error: (error) => {
        this.error.set(aedErrorMessage(error));
        this.busy.set(false);
        this.focus('#aed-conv-error');
      },
    });
  }

  private form(file: File): FormData {
    const body = new FormData();
    body.append('plik', file, file.name);
    return body;
  }
}
