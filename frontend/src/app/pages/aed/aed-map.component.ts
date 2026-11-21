import {
  AfterViewInit,
  Component,
  effect,
  ElementRef,
  inject,
  input,
  NgZone,
  OnDestroy,
  signal,
  untracked,
  viewChild,
} from '@angular/core';
import * as L from 'leaflet';

import { AedApiService, aedErrorMessage, AedMapFeature, AedStatus } from './aed-api.service';
import { AED_OPEN_LABELS, aedOpenNow, AedOpenState, aedWarsawNow } from './aed-hours';
import { aedField } from './aed-schema';
import { AED_STATUS_LABELS, AED_STATUS_PATHS } from './aed-status.component';

/** Points closer than this many screen pixels are drawn as one numbered group. */
const CELL = 72;

/**
 * Map of the registry, an addition to the accessible list. Points come from /urzadzenia.geojson for the
 * visible area; nearby points are grouped on screen, so a view never holds more than a few hundred markers.
 */
@Component({
  selector: 'app-aed-map',
  standalone: true,
  template: `
    <fieldset class="aed-filter">
      <legend class="aed-filter__legend">Pokaż na mapie według dostępności teraz</legend>
      <label class="aed-filter__option">
        <input type="radio" name="aed-open" value="" [checked]="open() === ''" (change)="open.set('')" />
        <span>Wszystkie</span>
      </label>
      @for (state of states; track state) {
        <label class="aed-filter__option">
          <input type="radio" name="aed-open" [value]="state" [checked]="open() === state" (change)="open.set(state)" />
          <span>{{ openLabels[state] }}</span>
        </label>
      }
    </fieldset>
    <p class="aed-note">
      Dostępność wynika z godzin podanych w rejestrze i z bieżącej godziny w Polsce. Gdy godzin nie podano albo nie da
      się ich jednoznacznie odczytać, urządzenie ma stan „nieznana”.
    </p>
    @if (error()) {
      <p class="aed-message aed-message--error" role="alert">{{ error() }}</p>
    }
    <p class="aed-count">{{ summary() }}</p>
    <p class="aed-note">
      Klawiatura: Tab przechodzi po znacznikach, Enter otwiera opis urządzenia albo przybliża grupę, Escape zamyka opis.
      Gdy mapa ma fokus, strzałki ją przesuwają, a plus i minus zmieniają powiększenie.
    </p>
    <div class="aed-map__canvas" #canvas role="region" aria-label="Mapa defibrylatorów AED"></div>
  `,
})
export class AedMapComponent implements AfterViewInit, OnDestroy {
  private readonly api = inject(AedApiService);
  private readonly zone = inject(NgZone);
  private readonly canvas = viewChild.required<ElementRef<HTMLElement>>('canvas');

  /** Status chosen in the registry filter; the map follows it. */
  readonly status = input<AedStatus | ''>('');

  protected readonly states: AedOpenState[] = ['dostepny', 'zamkniety', 'nieznane'];
  protected readonly openLabels = AED_OPEN_LABELS;
  protected readonly open = signal<AedOpenState | ''>('');
  protected readonly summary = signal('Wczytuję mapę…');
  protected readonly error = signal('');

  private map: L.Map;
  private readonly markers = L.layerGroup();
  private features: AedMapFeature[] = [];
  private loaded: L.LatLngBounds;
  private request = 0;
  private popup: L.Popup | null = null;

  constructor() {
    effect(() => {
      this.status();
      this.open();
      untracked(() => this.draw()); // draw() writes the summary signal
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
      this.markers.addTo(this.map);
      // An open popup pans the map to fit; redrawing then would remove its marker and close it.
      this.map.on('moveend', () => this.popup || this.load());
      this.map.on('popupopen', (event) => {
        this.popup = event.popup;
        // Keyboard: move focus into the popup so its text is read; Escape closes it.
        const box = event.popup.getElement();
        box.setAttribute('tabindex', '-1');
        box.focus({ preventScroll: true });
        // Leaflet listens for Escape only while the map itself has focus, so the popup closes itself.
        box.onkeydown = (key) => key.key === 'Escape' && this.map.closePopup();
      });
      this.map.on('popupclose', () => {
        this.popup = null;
        this.map.getContainer().focus({ preventScroll: true });
        this.load();
      });
      this.map.fitBounds([
        [lat.minimum, lon.minimum],
        [lat.maximum, lon.maximum],
      ]);
    });
  }

  ngOnDestroy(): void {
    this.map?.remove();
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
    const open = this.open();
    const now = aedWarsawNow();
    const openStates = new Map<string, AedOpenState>(); // many devices share the same hours text
    const openState = (hours: string) =>
      openStates.get(hours) ?? openStates.set(hours, aedOpenNow(hours, now)).get(hours);

    const zoom = this.map.getZoom();
    const view = this.map.getBounds();
    const cells = new Map<string, AedMapFeature[]>();
    let count = 0;
    for (const feature of this.features) {
      const [lng, lat] = feature.geometry.coordinates;
      const { properties } = feature;
      if (!view.contains([lat, lng])) continue;
      if (status && properties.status !== status) continue;
      if (open && openState(properties.godziny_dostepu) !== open) continue;
      count++;
      const point = this.map.project([lat, lng], zoom);
      const key = `${Math.floor(point.x / CELL)}:${Math.floor(point.y / CELL)}`;
      if (!cells.has(key)) cells.set(key, []);
      cells.get(key).push(feature);
    }

    this.markers.clearLayers();
    for (const group of cells.values()) {
      if (group.length === 1 || zoom >= this.map.getMaxZoom()) {
        group.forEach((feature) => this.markers.addLayer(this.device(feature, openState)));
      } else {
        this.markers.addLayer(this.group(group));
      }
    }
    this.summary.set(
      `Urządzenia w widocznym obszarze mapy: ${count.toLocaleString('pl-PL')}. ` +
        'Liczba w kółku oznacza grupę urządzeń – wybierz ją, aby przybliżyć.',
    );
  }

  private group(features: AedMapFeature[]): L.Marker {
    const points = features.map(({ geometry }) => L.latLng(geometry.coordinates[1], geometry.coordinates[0]));
    const bounds = L.latLngBounds(points);
    const size = features.length < 100 ? 36 : features.length < 1000 ? 44 : 52;
    const label = `${features.length.toLocaleString('pl-PL')} urządzeń w tym miejscu mapy – przybliż`;
    return L.marker(bounds.getCenter(), {
      title: label,
      alt: label,
      autoPanOnFocus: false, // every marker drawn is inside the view; panning would redraw and drop keyboard focus
      icon: L.divIcon({ className: 'aed-cluster', html: String(features.length), iconSize: [size, size] }),
    }).on('click keypress', () => {
      // The group marker disappears on zoom; keep keyboard focus on the map (arrow keys move it, + and - zoom).
      this.map.getContainer().focus({ preventScroll: true });
      this.map.fitBounds(bounds.pad(0.2));
    });
  }

  private device({ geometry, properties }: AedMapFeature, openState: (hours: string) => AedOpenState): L.Marker {
    const name = properties.nazwa || 'Miejsce bez nazwy';
    const label = `${name}, status: ${AED_STATUS_LABELS[properties.status]}`;
    return L.marker([geometry.coordinates[1], geometry.coordinates[0]], {
      title: label,
      alt: label,
      autoPanOnFocus: false, // every marker drawn is inside the view; panning would redraw and drop keyboard focus
      icon: L.divIcon({
        className: `aed-pin aed-pin--${properties.status}`,
        html: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${AED_STATUS_PATHS[properties.status]}"/></svg>`,
        iconSize: [28, 28],
      }),
    }).bindPopup(() => {
      // Built with textContent: names and hours come from open sources and must not be read as HTML.
      const box = document.createElement('div');
      const line = (tag: string, text: string) => {
        const element = document.createElement(tag);
        element.textContent = text;
        box.append(element);
      };
      line('strong', name);
      line('p', `Status: ${AED_STATUS_LABELS[properties.status]}`);
      line('p', `Dostęp: ${properties.dostep || 'brak danych'}`);
      line('p', `Godziny dostępu: ${properties.godziny_dostepu || 'brak danych'}`);
      line('p', `${AED_OPEN_LABELS[openState(properties.godziny_dostepu)]}`);
      line('p', `Kompletność danych: ${properties.kompletnosc}%`);
      line('p', properties.id_aed);
      return box;
    });
  }
}
