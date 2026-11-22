import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';

import { SeoService } from '@app/services/seo.service';
import { PaginationComponent } from '@app/shared/pagination/pagination.component';
import { AedApiService, aedErrorMessage, AedRecord, AedStatus } from './aed-api.service';
import { AED_OPEN_LABELS, aedOpenNow } from './aed-hours';
import { AedMapComponent } from './aed-map.component';
import { aedField, aedOptions } from './aed-schema';
import { AED_STATUS_LABELS, AedStatusComponent } from './aed-status.component';

/** National registry: an accessible list first, the map second. */
@Component({
  selector: 'app-aed-registry',
  standalone: true,
  imports: [AedStatusComponent, AedMapComponent, PaginationComponent],
  templateUrl: './aed-registry.component.html',
})
export class AedRegistryComponent implements OnInit {
  private readonly api = inject(AedApiService);
  private readonly seo = inject(SeoService);

  protected readonly perPage = 25;
  protected readonly statuses = aedOptions(aedField('status')) as AedStatus[];
  protected readonly labels = AED_STATUS_LABELS;
  protected readonly title = (column: string) => aedField(column).title;
  protected readonly number = (value: number) => value.toLocaleString('pl-PL');

  protected readonly stats = toSignal(this.api.stats());
  protected readonly status = signal<AedStatus | ''>('');
  protected readonly query = signal('');
  protected readonly openNowOnly = signal(false);
  protected readonly openLabel = AED_OPEN_LABELS.dostepny;
  /** Devices left out by the filter because their hours are unknown (only while the filter is on). */
  protected readonly withoutHours = signal<number | null>(null);
  protected readonly page = signal(1);
  protected readonly records = signal<AedRecord[]>([]);
  protected readonly total = signal(0);
  protected readonly error = signal('');
  protected readonly shown = computed(() => {
    const first = (this.page() - 1) * this.perPage + 1;
    const range = this.records().length ? `${first}–${first + this.records().length - 1}` : '0';
    const status = this.status() ? `, status: ${this.labels[this.status()]}` : '';
    const query = this.query() ? `, szukane: „${this.query()}”` : '';
    const open = this.openNowOnly() ? ', tylko dostępne teraz' : '';
    const unknown = this.withoutHours()
      ? ` Dla ${this.number(this.withoutHours())} urządzeń godziny dostępu nie są znane, więc nie ma ich na liście.`
      : '';
    return `Pokazano ${range} z ${this.number(this.total())}${status}${query}${open}.${unknown}`;
  });

  ngOnInit(): void {
    this.seo.setPageTitle('Rejestr AED');
    this.load();
  }

  /** Any change of filter or search goes back to the first page. */
  protected filter(change: { status?: AedStatus | ''; query?: string; openNow?: boolean }): void {
    if (change.status !== undefined) this.status.set(change.status);
    if (change.openNow !== undefined) this.openNowOnly.set(change.openNow);
    if (change.query !== undefined) this.query.set(change.query.trim());
    this.load();
  }

  protected load(page = 1): void {
    this.page.set(page);
    this.api
      .devices({
        status: this.status() || undefined,
        q: this.query(),
        dostepny_teraz: this.openNowOnly() ? 1 : undefined,
        strona: page,
        na_stronie: this.perPage,
      })
      .subscribe({
        next: (result) => {
          this.records.set(result.dane);
          this.total.set(result.razem);
          this.withoutHours.set(result.bez_godzin ?? null);
          this.error.set('');
        },
        error: (error) => this.error.set(aedErrorMessage(error)),
      });
  }

  protected openNow(record: AedRecord): string {
    return AED_OPEN_LABELS[aedOpenNow(record['godziny_dostepu'] as string)];
  }

  protected address(record: AedRecord): string {
    const street = [record['cecha_ulicy'], record['nazwa_ulicy'], record['nr_budynku']].filter(Boolean).join(' ');
    return [street, record['miejscowosc']].filter(Boolean).join(', ');
  }
}
