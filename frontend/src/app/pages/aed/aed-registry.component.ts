import {
  afterNextRender,
  Component,
  computed,
  ElementRef,
  inject,
  Injector,
  OnInit,
  signal,
  viewChild,
} from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { toSignal } from '@angular/core/rxjs-interop';
import { Subscription } from 'rxjs';

import { SeoService } from '@app/services/seo.service';
import { PaginationComponent } from '@app/shared/pagination/pagination.component';
import { AedApiService, aedErrorMessage, AedRecord, AedStatus } from './aed-api.service';
import { AED_SCHEDULE_LABELS, aedOpenNow, AedOpenState } from './aed-hours';
import { AedMapComponent, aedDistanceText, AedOrigin, aedPlaceTitle, aedRouteUrl } from './aed-map.component';
import { aedField, aedOptions } from './aed-schema';
import { AED_STATUS_LABELS, AedStatusComponent } from './aed-status.component';

/** National registry: an accessible list first, the map second. */
@Component({
  selector: 'app-aed-registry',
  standalone: true,
  imports: [AedStatusComponent, AedMapComponent, PaginationComponent, NgTemplateOutlet],
  templateUrl: './aed-registry.component.html',
})
export class AedRegistryComponent implements OnInit {
  private readonly api = inject(AedApiService);
  private readonly seo = inject(SeoService);
  private readonly injector = inject(Injector);
  private readonly map = viewChild(AedMapComponent);
  private readonly search = viewChild<ElementRef<HTMLInputElement>>('search');

  private listRequest?: Subscription;

  protected readonly perPage = 25;
  protected readonly statuses = aedOptions(aedField('status')) as AedStatus[];
  protected readonly labels = AED_STATUS_LABELS;
  protected readonly title = (column: string) => aedField(column).title;
  protected readonly number = (value: number) => value.toLocaleString('pl-PL');
  protected readonly distanceText = aedDistanceText;

  protected readonly stats = toSignal(this.api.stats());
  protected readonly status = signal<AedStatus | ''>('');
  protected readonly query = signal('');
  protected readonly openNowOnly = signal(false);
  protected readonly schedule = AED_SCHEDULE_LABELS;
  protected readonly placeTitle = aedPlaceTitle;
  protected readonly routeUrl = aedRouteUrl;
  /** "Twojej lokalizacji" / "wybranego punktu" for the sentence above the sorted list. */
  protected readonly fromText = (origin: AedOrigin) =>
    origin.accuracy !== undefined ? 'Twojej lokalizacji' : 'wybranego punktu';
  /** Point the list is sorted from; kept only in this component, sent only as `lat`/`lon` of the list request. */
  protected readonly origin = signal<AedOrigin | null>(null);
  protected readonly picking = signal(false);
  protected readonly locating = signal(false);
  protected readonly nearError = signal('');
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
    const open = this.openNowOnly() ? ', tylko dostępne teraz według harmonogramu' : '';
    const near = this.origin() ? ', od najbliższego (odległość w linii prostej)' : '';
    const unknown = this.withoutHours()
      ? ` Dla ${this.number(this.withoutHours())} urządzeń godziny dostępu nie są znane, więc nie ma ich na liście.`
      : '';
    return `Pokazano ${range} z ${this.number(this.total())}${status}${query}${open}${near}.${unknown}`;
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

  protected load(page = 1, focusId = ''): void {
    this.page.set(page);
    const origin = this.origin();
    // Only the latest request may fill the list: an older answer (e.g. sorted by distance) must not arrive last.
    this.listRequest?.unsubscribe();
    this.listRequest = this.api
      .devices({
        status: this.status() || undefined,
        q: this.query(),
        dostepny_teraz: this.openNowOnly() ? 1 : undefined,
        lat: origin ? +origin.lat.toFixed(5) : undefined,
        lon: origin ? +origin.lon.toFixed(5) : undefined,
        strona: page,
        na_stronie: this.perPage,
      })
      .subscribe({
        next: (result) => {
          this.records.set(result.dane);
          this.total.set(result.razem);
          this.withoutHours.set(result.bez_godzin ?? null);
          this.error.set('');
          if (focusId) {
            afterNextRender(() => document.getElementById(`aed-row-${focusId}`)?.focus(), { injector: this.injector });
          }
        },
        error: (error) => this.error.set(aedErrorMessage(error)),
      });
  }

  protected locate(): void {
    this.nearError.set('');
    if (!navigator.geolocation) {
      this.nearError.set('Ta przeglądarka nie udostępnia lokalizacji. Wskaż punkt na mapie.');
      return;
    }
    this.locating.set(true);
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        this.locating.set(false);
        this.setOrigin({ lat: coords.latitude, lon: coords.longitude, accuracy: Math.round(coords.accuracy) });
      },
      (failure) => {
        this.locating.set(false);
        this.nearError.set(
          failure.code === failure.PERMISSION_DENIED
            ? 'Przeglądarka nie zezwoliła na użycie lokalizacji. Wskaż punkt na mapie albo zmień uprawnienie strony.'
            : 'Nie udało się ustalić lokalizacji. Spróbuj ponownie albo wskaż punkt na mapie.',
        );
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 },
    );
  }

  protected setOrigin(origin: AedOrigin | null): void {
    this.picking.set(false);
    this.nearError.set('');
    this.origin.set(origin);
    this.load();
  }

  /** "Pokaż na liście" of the map panel: search the list for this id and move focus to its row. */
  protected showOnList(id: string): void {
    const search = this.search()?.nativeElement;
    if (search) search.value = id;
    this.query.set(id);
    this.load(1, id);
  }

  protected showOnMap(record: AedRecord): void {
    this.map()?.showDevice(record.id_aed, +record['szerokosc_geograficzna'], +record['dlugosc_geograficzna']);
  }

  protected hasPoint(record: AedRecord): boolean {
    return !!record['szerokosc_geograficzna'] && !!record['dlugosc_geograficzna'];
  }

  protected openState(record: AedRecord): AedOpenState {
    return aedOpenNow(record['godziny_dostepu'] as string);
  }

  protected address(record: AedRecord): string {
    const street = [record['cecha_ulicy'], record['nazwa_ulicy'], record['nr_budynku']].filter(Boolean).join(' ');
    return [street, record['miejscowosc']].filter(Boolean).join(', ');
  }
}
