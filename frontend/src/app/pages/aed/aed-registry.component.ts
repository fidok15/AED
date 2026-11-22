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
import { ActivatedRoute } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { Subscription } from 'rxjs';

import { SeoService } from '@app/services/seo.service';
import { PaginationComponent } from '@app/shared/pagination/pagination.component';
import { AedApiService, aedErrorMessage, AedFilters, AedRecord, AedStatus } from './aed-api.service';
import { AED_SCHEDULE_LABELS, aedOpenNow, AedOpenState } from './aed-hours';
import {
  aedDistanceText,
  aedFloorText,
  AedMapComponent,
  AedOrigin,
  aedPlaceTitle,
  aedPositionText,
  aedRouteUrl,
} from './aed-map.component';
import { aedField, aedLabel, aedOptions } from './aed-schema';
import {
  AED_STATUS_LABELS,
  AedConditionComponent,
  aedConditionText,
  AedStatusComponent,
  aedUnavailable,
} from './aed-status.component';

/** Extra filters of the registry, folded under "Dodatkowe filtry". */
type AedExtraFilters = Omit<AedFilters, 'status' | 'dostepny_teraz'>;

/** National registry: the map on top, the accessible list with every device below it (a skip link leads there). */
@Component({
  selector: 'app-aed-registry',
  standalone: true,
  imports: [AedStatusComponent, AedConditionComponent, AedMapComponent, PaginationComponent, NgTemplateOutlet],
  templateUrl: './aed-registry.component.html',
})
export class AedRegistryComponent implements OnInit {
  private readonly api = inject(AedApiService);
  private readonly seo = inject(SeoService);
  private readonly injector = inject(Injector);
  private readonly route = inject(ActivatedRoute);
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
  protected readonly options = toSignal(this.api.filterOptions());
  /** Public access values of the schema; `prywatny` devices are never listed. */
  protected readonly access = aedOptions(aedField('dostep')).filter((value) => value !== 'prywatny');
  /** Short label: the schema label up to its explanation ("Publiczny – każdy …" -> "Publiczny"). */
  protected readonly accessLabel = (value: string) => aedLabel(aedField('dostep'), value).split(' – ')[0];
  /** Device conditions of the schema enum, in the order of the schema. */
  protected readonly conditions = aedOptions(aedField('stan_urzadzenia'));
  protected readonly unavailable = aedUnavailable;
  protected readonly conditionText = aedConditionText;
  protected readonly floorText = aedFloorText;
  protected readonly positionText = aedPositionText;
  protected readonly inside = [
    { value: 'tak', label: 'W budynku' },
    { value: 'nie', label: 'Na zewnątrz' },
  ];
  protected readonly extra = signal<AedExtraFilters>({});
  protected readonly extraCount = computed(() => Object.values(this.extra()).filter(Boolean).length);
  /** The one set of filters: the list request and the map points both use it. */
  protected readonly filters = computed<AedFilters>(() => ({
    status: this.status() || undefined,
    dostepny_teraz: this.openNowOnly() ? 1 : undefined,
    ...this.extra(),
  }));
  /** Models of the chosen producer (letter case ignored, as the service compares), else all of them. */
  protected readonly models = computed(() => {
    const producer = this.extra().producent?.toLowerCase();
    return (this.options()?.model ?? []).filter((item) => !producer || item.producent.toLowerCase() === producer);
  });
  protected readonly withProducer = computed(() => this.sum(this.options()?.producent));
  protected readonly withModel = computed(() => this.sum(this.options()?.model));
  protected readonly withTown = computed(() => this.sum(this.options()?.miejscowosc));
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
    const extra = this.extraCount() ? `, dodatkowe filtry: ${this.extraCount()}` : '';
    const unknown = this.withoutHours()
      ? ` Dla ${this.number(this.withoutHours())} urządzeń godziny dostępu nie są znane, więc nie ma ich na liście.`
      : '';
    return `Pokazano ${range} z ${this.number(this.total())}${status}${query}${open}${extra}${near}.${unknown}`;
  });

  ngOnInit(): void {
    this.seo.setPageTitle(['Rejestr urządzeń', 'Opiekun AED']);
    this.load();
    // "Znajdź najbliższy AED" on the start page lands on the location button, ready for Enter.
    if (this.route.snapshot.fragment === 'aed-near') {
      afterNextRender(() => document.getElementById('aed-locate')?.focus(), { injector: this.injector });
    }
  }

  /** Any change of filter or search goes back to the first page. */
  protected filter(change: { status?: AedStatus | ''; query?: string; openNow?: boolean }): void {
    if (change.status !== undefined) this.status.set(change.status);
    if (change.openNow !== undefined) this.openNowOnly.set(change.openNow);
    if (change.query !== undefined) this.query.set(change.query.trim());
    this.load();
  }

  /** One extra filter changed; a model of another producer no longer applies. */
  protected setExtra(name: keyof AedExtraFilters, value: string | 1 | undefined): void {
    const next: AedExtraFilters = { ...this.extra(), [name]: value || undefined };
    this.extra.set(next);
    if (name === 'producent' && next.model && !this.models().some((item) => item.wartosc === next.model)) {
      this.extra.set({ ...next, model: undefined });
    }
    this.load();
  }

  protected clearExtra(): void {
    if (!this.extraCount()) return;
    this.extra.set({});
    this.load();
  }

  protected check(event: Event): 1 | undefined {
    return (event.target as HTMLInputElement).checked ? 1 : undefined;
  }

  /** "Przejdź do listy urządzeń": focus the list heading, as the portal's own skip links do. */
  protected skipToList(event: Event): void {
    event.preventDefault();
    document.getElementById('aed-list-heading')?.focus();
  }

  protected load(page = 1, focusId = ''): void {
    this.page.set(page);
    const origin = this.origin();
    // Only the latest request may fill the list: an older answer (e.g. sorted by distance) must not arrive last.
    this.listRequest?.unsubscribe();
    this.listRequest = this.api
      .devices({
        ...this.filters(),
        q: this.query(),
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
    // Distances on screen belong to the previous origin: never show them under the new origin label.
    this.records.set([]);
    this.total.set(0);
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

  private sum(items: { liczba: number }[] | undefined): number {
    return (items ?? []).reduce((total, item) => total + item.liczba, 0);
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
