import {
  afterNextRender,
  AfterViewInit,
  Component,
  computed,
  effect,
  ElementRef,
  inject,
  Injector,
  input,
  NgZone,
  OnDestroy,
  output,
  signal,
  untracked,
  viewChild,
} from '@angular/core';
import * as L from 'leaflet';

import { AedApiService, aedErrorMessage, AedMapFeature, AedRecord, AedStatus } from './aed-api.service';
import { AED_SCHEDULE_LABELS, aedOpenNow, AedOpenState, aedWarsawNow } from './aed-hours';
import { aedField } from './aed-schema';
import { AED_MARKS, AED_STATUS_LABELS, aedMarkSvg, AedStatusComponent } from './aed-status.component';

/** Point the list and the map are measured from: the phone's position or a point picked on the map. */
export interface AedOrigin {
  lat: number;
  lon: number;
  /** Radius in metres, only for a position from the phone. */
  accuracy?: number;
}

/** Straight-line distance in metres (haversine, as aed_standard.sources.haversine_m). */
export function aedDistanceM(from: AedOrigin, lat: number, lon: number): number {
  const rad = Math.PI / 180;
  const a =
    Math.sin(((lat - from.lat) * rad) / 2) ** 2 +
    Math.cos(from.lat * rad) * Math.cos(lat * rad) * Math.sin(((lon - from.lon) * rad) / 2) ** 2;
  return 2 * 6371008.8 * Math.asin(Math.sqrt(a));
}

export const aedDistanceText = (metres: number): string =>
  (metres < 1000
    ? `${Math.round(metres)} m`
    : `${(metres / 1000).toLocaleString('pl-PL', { maximumFractionDigits: 1 })} km`) + ' w linii prostej';

/** "1 urządzenie", "3 urządzenia", "12 urządzeń". */
export function aedDevices(count: number): string {
  const n = count.toLocaleString('pl-PL');
  if (count === 1) return `${n} urządzenie`;
  const few = count % 10 >= 2 && count % 10 <= 4 && (count % 100 < 12 || count % 100 > 14);
  return `${n} ${few ? 'urządzenia' : 'urządzeń'}`;
}

/** Heading of a device: its name, else where it is, a placeholder only when nothing is known. */
export const aedPlaceTitle = (name: unknown, ...where: unknown[]): string =>
  [name, ...where].map((v) => String(v ?? '').trim()).find(Boolean) || 'Miejsce bez nazwy';

/** Directions to the device in the map service of the phone; only the destination goes into the address. */
export const aedRouteUrl = (lat: number | string, lon: number | string): string =>
  `https://www.google.com/maps/dir/?api=1&destination=${+lat},${+lon}`;

/** "Twoja lokalizacja" for a position from the phone (it has an accuracy), "Wybrany punkt" for a picked one. */
export const aedOriginName = (origin: AedOrigin | null): string =>
  !origin
    ? 'Twoja lokalizacja albo wybrany punkt'
    : origin.accuracy !== undefined
      ? 'Twoja lokalizacja'
      : 'Wybrany punkt';

/** Grouping radius in screen pixels: wide on the country view, just above a marker's size in a city. */
const radiusFor = (zoom: number) => (zoom <= 7 ? 72 : zoom <= 11 ? 56 : zoom <= 13 ? 44 : 28);

const latLng = (feature: AedMapFeature) => L.latLng(feature.geometry.coordinates[1], feature.geometry.coordinates[0]);

/**
 * Map of the registry, an addition to the accessible list. Points come from /urzadzenia.geojson for the
 * visible area (the whole country is ~15 800 points, one request); points closer than a grid cell are drawn
 * as one numbered disc, so a view never holds more than a few hundred markers.
 */
@Component({
  selector: 'app-aed-map',
  standalone: true,
  imports: [AedStatusComponent],
  // Escape closes the details from anywhere in the map (the panel, a marker, the map itself).
  host: { '(keydown.escape)': 'selected() && close()' },
  template: `
    @if (error()) {
      <p class="aed-message aed-message--error" role="alert">{{ error() }}</p>
    }
    <details class="aed-legend" open>
      <summary>Legenda mapy</summary>
      <ul class="aed-legend__list">
        @for (item of legend; track item) {
          <li>
            <app-aed-status [status]="item" />
            @if (item === 'wycofany') {
              <span class="aed-note">(widoczny po wybraniu tego statusu)</span>
            }
          </li>
        }
        <li>
          <span class="aed-cluster aed-cluster--sample" aria-hidden="true">12</span>
          <span>Grupa urządzeń – wybierz, aby przybliżyć</span>
        </li>
        <li>
          <span class="aed-here aed-here--sample" aria-hidden="true"></span>
          <span>{{ originName(origin()) }}</span>
        </li>
      </ul>
      <p class="aed-note">
        Klawiatura: Tab przechodzi po znacznikach, Enter otwiera opis urządzenia albo przybliża grupę, Escape zamyka
        opis. Gdy mapa ma fokus, strzałki ją przesuwają, a plus i minus zmieniają powiększenie.
      </p>
    </details>
    <p class="aed-count">{{ summary() }}</p>
    @if (picking()) {
      <p class="aed-message" role="status">
        Kliknij miejsce na mapie albo przesuń mapę strzałkami i naciśnij Enter, aby wybrać punkt pod krzyżykiem.
      </p>
    }
    <div class="aed-map__frame" [class.aed-map__frame--picking]="picking()">
      <div
        class="aed-map__canvas"
        #canvas
        tabindex="0"
        role="region"
        aria-label="Mapa defibrylatorów AED"
        (keydown.enter)="pickCentre($event)"></div>
      @if (selected(); as group) {
        <section class="aed-map__panel" aria-labelledby="aed-panel-title">
          @if (group.length > 1) {
            <h3 class="aed-map__title" id="aed-panel-title" tabindex="-1" #panelTitle>
              {{ devicesText(group.length) }} w tym samym miejscu
            </h3>
            <ul class="aed-map__stack">
              @for (feature of group; track feature.properties.id_aed) {
                <li>
                  <button type="button" class="btn btn-link" (click)="choose(feature)">
                    {{ feature.properties.nazwa || 'Miejsce bez nazwy' }}
                  </button>
                  <app-aed-status [status]="feature.properties.status" />
                </li>
              }
            </ul>
          } @else {
            @let point = group[0].properties;
            @let at = group[0].geometry.coordinates;
            <h3 class="aed-map__title" id="aed-panel-title" tabindex="-1" #panelTitle>
              {{ placeTitle(point.nazwa, detail() && address(detail()), detail()?.['opis_lokalizacji']) }}
            </h3>
            <app-aed-status [status]="point.status" />
            @if (distance()) {
              <p class="aed-map__distance">{{ distance() }}</p>
            }
            @if (detail(); as record) {
              @if (address(record)) {
                <p>{{ address(record) }}</p>
              }
              @if (record['opis_lokalizacji']) {
                <p>{{ record['opis_lokalizacji'] }}</p>
              }
            }
            <dl class="aed-map__facts">
              <div>
                <dt>{{ title('godziny_dostepu') }}</dt>
                <dd>{{ point.godziny_dostepu || 'brak danych' }}</dd>
              </div>
              <div>
                <dt>{{ title('dostep') }}</dt>
                <dd>{{ point.dostep || 'brak danych' }}</dd>
              </div>
            </dl>
            <p class="aed-open aed-open--{{ openState(point.godziny_dostepu) }}">
              {{ schedule[openState(point.godziny_dostepu)] }}
            </p>
            <p class="aed-row__id">{{ point.id_aed }}</p>
            <a class="aed-route" [href]="routeUrl(at[1], at[0])" target="_blank" rel="noopener">
              Wyznacz trasę<span class="visually-hidden"> (Mapy Google, nowa karta)</span>
            </a>
            <button type="button" class="btn btn-link aed-map__to-list" (click)="showOnList.emit(point.id_aed)">
              Pokaż na liście
            </button>
          }
          <button type="button" class="btn btn-outline-primary aed-map__close" (click)="close()">Zamknij</button>
        </section>
      }
    </div>
  `,
})
export class AedMapComponent implements AfterViewInit, OnDestroy {
  private readonly api = inject(AedApiService);
  private readonly zone = inject(NgZone);
  private readonly injector = inject(Injector);
  private readonly canvas = viewChild.required<ElementRef<HTMLElement>>('canvas');
  private readonly panelTitle = viewChild<ElementRef<HTMLElement>>('panelTitle');

  /** Status chosen in the registry filter; the map follows it. */
  readonly status = input<AedStatus | ''>('');
  /** "Dostępny teraz" chosen above the list; same rule as `dostepny_teraz=1` of the API (aed_standard/hours.py). */
  readonly openNow = input(false);
  /** Point chosen above the list ("Użyj mojej lokalizacji" or picked here); the map centres on it. */
  readonly origin = input<AedOrigin | null>(null);
  /** While true, a click (or Enter on the map) picks the point under it and emits `picked`. */
  readonly picking = input(false);
  readonly picked = output<AedOrigin>();
  readonly showOnList = output<string>();

  protected readonly labels = AED_STATUS_LABELS;
  protected readonly schedule = AED_SCHEDULE_LABELS;
  protected readonly legend: AedStatus[] = ['aktywny', 'niepotwierdzony', 'zgloszony', 'nieaktualny', 'wycofany'];
  protected readonly title = (column: string) => aedField(column).title;
  protected readonly devicesText = aedDevices;
  protected readonly placeTitle = aedPlaceTitle;
  protected readonly routeUrl = aedRouteUrl;
  protected readonly originName = aedOriginName;
  protected readonly summary = signal('Wczytuję mapę…');
  protected readonly error = signal('');
  /** Devices shown in the panel: one device, or several at the same coordinates. */
  protected readonly selected = signal<AedMapFeature[] | null>(null);
  protected readonly detail = signal<AedRecord | null>(null);
  protected readonly distance = computed(() => {
    const origin = this.origin();
    const group = this.selected();
    if (!origin || group?.length !== 1) return '';
    const [lon, lat] = group[0].geometry.coordinates;
    return aedDistanceText(aedDistanceM(origin, lat, lon));
  });

  private map: L.Map;
  private readonly markers = L.layerGroup();
  private readonly here = L.layerGroup();
  private features: AedMapFeature[] = [];
  private loaded: L.LatLngBounds;
  private request = 0;
  /** Marker drawn for each device id (its own marker or the group it is in), to give focus back. */
  private markerOf = new Map<string, L.Marker>();
  private groupOf = new Map<string, AedMapFeature[]>();
  /** Device whose marker opened the panel; focus returns to it. */
  private trigger = '';
  /** Device asked for by "Pokaż na mapie", opened once its point is loaded. */
  private pending = '';
  private openStates = new Map<string, AedOpenState>();

  constructor() {
    effect(() => {
      this.status();
      this.openNow();
      untracked(() => this.draw()); // draw() writes the summary signal
    });
    effect(() => {
      const origin = this.origin();
      untracked(() => this.showOrigin(origin));
    });
    effect(() => {
      // Picking starts from a button above the list: bring the map into view and give it the keyboard.
      if (this.picking()) this.canvas().nativeElement.focus();
    });
  }

  ngAfterViewInit(): void {
    // Poland, from the coordinate limits of the standard.
    const lat = aedField('szerokosc_geograficzna').constraints;
    const lon = aedField('dlugosc_geograficzna').constraints;
    this.zone.runOutsideAngular(() => {
      this.map = L.map(this.canvas().nativeElement, { maxZoom: 18, minZoom: 5 });
      this.map.attributionControl.setPrefix(false);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }).addTo(this.map);
      this.here.addTo(this.map);
      this.markers.addTo(this.map);
      this.map.on('moveend', () => this.load());
      this.map.on('click', (event: L.LeafletMouseEvent) => {
        if (this.picking()) this.zone.run(() => this.picked.emit({ lat: event.latlng.lat, lon: event.latlng.lng }));
      });
      this.map.fitBounds([
        [lat.minimum, lon.minimum],
        [lat.maximum, lon.maximum],
      ]);
      this.showOrigin(this.origin());
    });
  }

  ngOnDestroy(): void {
    this.map?.remove();
  }

  /** "Pokaż na mapie" of the list: zoom in on the device and open its panel. */
  showDevice(id: string, lat: number, lon: number): void {
    this.pending = id;
    this.canvas().nativeElement.scrollIntoView({ block: 'center' });
    this.map.setView([lat, lon], 17);
    this.load();
  }

  protected pickCentre(event: Event): void {
    if (!this.picking() || event.target !== this.canvas().nativeElement) return;
    const centre = this.map.getCenter();
    this.picked.emit({ lat: centre.lat, lon: centre.lng });
  }

  protected choose(feature: AedMapFeature): void {
    this.open([feature]);
  }

  protected close(): void {
    this.selected.set(null);
    this.draw();
    const marker = this.markerOf.get(this.trigger)?.getElement();
    (marker ?? this.canvas().nativeElement).focus({ preventScroll: true });
  }

  protected openState(hours: string): AedOpenState {
    return this.openStates.get(hours) ?? this.openStates.set(hours, aedOpenNow(hours, aedWarsawNow())).get(hours);
  }

  protected address(record: AedRecord): string {
    const street = [record['cecha_ulicy'], record['nazwa_ulicy'], record['nr_budynku']].filter(Boolean).join(' ');
    const town = [record['kod_pocztowy'], record['miejscowosc']].filter(Boolean).join(' ');
    return [street, town].filter(Boolean).join(', ');
  }

  private open(group: AedMapFeature[]): void {
    this.zone.run(() => {
      this.selected.set(group);
      this.detail.set(null);
      if (group.length === 1) {
        const id = group[0].properties.id_aed;
        this.api
          .device(id)
          .subscribe({ next: (record) => this.selected()?.[0] === group[0] && this.detail.set(record) });
      }
      this.draw();
      afterNextRender(() => this.panelTitle()?.nativeElement.focus(), { injector: this.injector });
    });
  }

  private showOrigin(origin: AedOrigin | null): void {
    if (!this.map) return;
    this.here.clearLayers();
    if (!origin) return;
    const point: L.LatLngExpression = [origin.lat, origin.lon];
    if (origin.accuracy) {
      L.circle(point, { radius: origin.accuracy, className: 'aed-here-accuracy', interactive: false }).addTo(this.here);
    }
    L.marker(point, {
      icon: L.divIcon({ className: 'aed-here', iconSize: [20, 20] }),
      interactive: false,
      keyboard: false,
      zIndexOffset: -1000,
    })
      .on('add', (event) => {
        const element = (event.target as L.Marker).getElement();
        element?.setAttribute('role', 'img');
        element?.setAttribute('aria-label', aedOriginName(origin));
      })
      .addTo(this.here);
    this.map.setView(point, Math.max(this.map.getZoom(), 15));
  }

  /** Fetch the points of the visible area, with a margin so that small moves need no new request. */
  private load(): void {
    const view = this.map.getBounds();
    if (this.loaded?.contains(view)) return this.draw();
    const area = view.pad(0.5);
    const bbox = [area.getWest(), area.getSouth(), area.getEast(), area.getNorth()].map((v) => v.toFixed(4)).join();
    const request = ++this.request;
    this.api.mapPoints(bbox).subscribe({
      next: (features) => {
        if (request !== this.request) return; // an older answer arrived late
        this.features = features;
        this.loaded = area;
        this.error.set('');
        this.draw();
      },
      error: (error) => this.error.set(aedErrorMessage(error)),
    });
  }

  private draw(): void {
    if (!this.map || !this.loaded) return;
    const status = this.status();
    const open = this.openNow();
    this.openStates.clear(); // the current minute decides; rebuilt once per drawing

    const zoom = this.map.getZoom();
    const radius = radiusFor(zoom);
    const view = this.map.getBounds();
    // Greedy grouping: a point joins the first group whose seed is within `radius` pixels, else seeds a new one.
    // Seeds are at least `radius` apart, so discs do not pile up; the grid only limits the search to 3×3 cells.
    const seeds = new Map<string, { x: number; y: number; features: AedMapFeature[] }[]>();
    const groups: AedMapFeature[][] = [];
    let count = 0;
    for (const feature of this.features) {
      const [lng, lat] = feature.geometry.coordinates;
      const { properties } = feature;
      if (!view.contains([lat, lng])) continue;
      if (status ? properties.status !== status : properties.status === 'wycofany') continue;
      if (open && this.openState(properties.godziny_dostepu) !== 'dostepny') continue;
      count++;
      const point = this.map.project([lat, lng], zoom);
      const gx = Math.floor(point.x / radius);
      const gy = Math.floor(point.y / radius);
      let seed: { x: number; y: number; features: AedMapFeature[] } | undefined;
      for (let dx = -1; dx <= 1 && !seed; dx++) {
        for (let dy = -1; dy <= 1 && !seed; dy++) {
          seed = seeds
            .get(`${gx + dx}:${gy + dy}`)
            ?.find((s) => (s.x - point.x) ** 2 + (s.y - point.y) ** 2 < radius * radius);
        }
      }
      if (seed) {
        seed.features.push(feature);
        continue;
      }
      seed = { x: point.x, y: point.y, features: [feature] };
      const key = `${gx}:${gy}`;
      seeds.set(key, [...(seeds.get(key) ?? []), seed]);
      groups.push(seed.features);
    }

    this.markers.clearLayers();
    this.markerOf.clear();
    this.groupOf.clear();
    const chosen = this.selected();
    for (const group of groups) {
      const [first] = group;
      const sameSpot = group.every((f) => latLng(f).distanceTo(latLng(first)) < 1);
      let marker: L.Marker;
      if (group.length === 1) marker = this.device(first, chosen?.includes(first));
      else if (sameSpot || zoom >= this.map.getMaxZoom()) marker = this.stack(group);
      else marker = this.cluster(group);
      this.markers.addLayer(marker);
      for (const feature of group) {
        this.markerOf.set(feature.properties.id_aed, marker);
        this.groupOf.set(feature.properties.id_aed, group);
      }
    }

    const origin = this.origin() ? ` Środek mapy: ${aedOriginName(this.origin()).toLowerCase()}.` : '';
    this.summary.set(`Urządzenia w widocznym obszarze mapy: ${count.toLocaleString('pl-PL')}.${origin}`);

    if (this.pending && this.groupOf.has(this.pending)) {
      const id = this.pending;
      this.trigger = id;
      this.pending = '';
      this.open(this.groupOf.get(id).filter((feature) => feature.properties.id_aed === id));
    }
  }

  private marker(at: L.LatLng, label: string, icon: L.DivIcon, activate: () => void): L.Marker {
    return L.marker(at, {
      title: label,
      icon,
      autoPanOnFocus: false, // every marker drawn is inside the view; panning would redraw and drop keyboard focus
    })
      .on('add', (event) => (event.target as L.Marker).getElement()?.setAttribute('aria-label', label))
      .on('click', activate)
      .on('keypress', (event: L.LeafletKeyboardEvent) => {
        const key = event.originalEvent.key;
        if (key !== 'Enter' && key !== ' ') return;
        event.originalEvent.preventDefault();
        activate();
      });
  }

  /** Several devices near each other: zoom in on them. */
  private cluster(group: AedMapFeature[]): L.Marker {
    const points = group.map(latLng);
    const bounds = L.latLngBounds(points);
    const centre = L.latLng(
      points.reduce((sum, p) => sum + p.lat, 0) / points.length,
      points.reduce((sum, p) => sum + p.lng, 0) / points.length,
    );
    const size = group.length < 10 ? 28 : group.length < 100 ? 38 : group.length < 1000 ? 46 : 54;
    const label = `${aedDevices(group.length)} w tym obszarze – przybliż`;
    const icon = L.divIcon({
      className: 'aed-cluster',
      html: group.length.toLocaleString('pl-PL'),
      iconSize: [size, size],
    });
    return this.marker(centre, label, icon, () => {
      // The group marker disappears on zoom; keep keyboard focus on the map (arrow keys move it, + and - zoom).
      this.canvas().nativeElement.focus({ preventScroll: true });
      this.map.fitBounds(bounds.pad(0.3), { maxZoom: this.map.getMaxZoom() });
    });
  }

  /** Devices at one spot (one building): a disc that lists them. */
  private stack(group: AedMapFeature[]): L.Marker {
    const label = `${aedDevices(group.length)} w tym samym miejscu – pokaż listę`;
    const icon = L.divIcon({
      className: 'aed-cluster aed-cluster--stack',
      html: group.length.toLocaleString('pl-PL'),
      iconSize: [28, 28],
    });
    return this.marker(latLng(group[0]), label, icon, () => {
      this.trigger = group[0].properties.id_aed;
      this.open(group);
    });
  }

  private device(feature: AedMapFeature, selected: boolean): L.Marker {
    const { properties } = feature;
    const mark = AED_MARKS[properties.status];
    const label = `${properties.nazwa || 'Miejsce bez nazwy'}, status: ${AED_STATUS_LABELS[properties.status]}`;
    const icon = L.divIcon({
      className: `aed-mark aed-mark--${properties.status}${selected ? ' aed-mark--selected' : ''}`,
      html: aedMarkSvg(mark),
      iconSize: mark.size,
      iconAnchor: mark.anchor,
    });
    return this.marker(latLng(feature), label, icon, () => {
      this.trigger = properties.id_aed;
      this.open([feature]);
    }).setZIndexOffset(properties.status === 'aktywny' ? 500 : 0);
  }
}
