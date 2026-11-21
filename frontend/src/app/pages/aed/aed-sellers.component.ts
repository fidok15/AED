import {
  AfterViewInit,
  Component,
  computed,
  ElementRef,
  inject,
  OnDestroy,
  OnInit,
  signal,
  viewChild,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import { LocalizeRouterPipe } from '@gilsdav/ngx-translate-router';
import * as L from 'leaflet';

import { SeoService } from '@app/services/seo.service';
import { AedApiService, aedErrorMessage, AedSellers } from './aed-api.service';
import { aedField } from './aed-schema';

/** Incentives: ranking of companies that report devices, with the badge for well-kept data. */
@Component({
  selector: 'app-aed-sellers',
  standalone: true,
  imports: [RouterLink, LocalizeRouterPipe],
  templateUrl: './aed-sellers.component.html',
})
export class AedSellersComponent implements OnInit, AfterViewInit, OnDestroy {
  private readonly api = inject(AedApiService);
  private readonly seo = inject(SeoService);
  private readonly canvas = viewChild.required<ElementRef<HTMLElement>>('canvas');
  private map: L.Map;

  protected readonly number = (value: number) => value.toLocaleString('pl-PL');
  protected readonly error = signal('');
  protected readonly sellers = signal<AedSellers | null>(null);
  /** Companies with at least one device, in ranking order; the rest are listed below without a place. */
  protected readonly ranked = computed(() => (this.sellers()?.dane ?? []).filter((seller) => seller.liczba_urzadzen));
  protected readonly waiting = computed(() => (this.sellers()?.dane ?? []).filter((seller) => !seller.liczba_urzadzen));

  ngOnInit(): void {
    this.seo.setPageTitle(['Firmy zgłaszające urządzenia', 'Rejestr AED']);
  }

  ngAfterViewInit(): void {
    const lat = aedField('szerokosc_geograficzna').constraints;
    const lon = aedField('dlugosc_geograficzna').constraints;
    this.map = L.map(this.canvas().nativeElement, { maxZoom: 12, minZoom: 5 });
    this.map.attributionControl.setPrefix(false);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(this.map);
    this.map.fitBounds([
      [lat.minimum, lon.minimum],
      [lat.maximum, lon.maximum],
    ]);

    this.api.sellers().subscribe({
      next: (sellers) => {
        this.sellers.set(sellers);
        for (const seller of sellers.dane) {
          const badge = seller.odznaka === 'tak' ? 'ma odznakę' : 'bez odznaki';
          const label = `${seller.nazwa}, ${seller.miejscowosc}, ${badge}`;
          // The pin carries the first letter of the company; a badge adds a check mark, not only a colour.
          L.marker([seller.szerokosc_geograficzna, seller.dlugosc_geograficzna], {
            title: label,
            alt: label,
            icon: L.divIcon({
              className: `aed-cluster${seller.odznaka === 'tak' ? ' aed-cluster--badge' : ''}`,
              html: seller.odznaka === 'tak' ? '✓' : seller.nazwa.charAt(0),
              iconSize: [36, 36],
            }),
          })
            .bindPopup(() => {
              const box = document.createElement('div');
              for (const [tag, text] of [
                ['strong', seller.nazwa],
                ['p', seller.miejscowosc],
                ['p', `Zgłoszone urządzenia: ${seller.liczba_urzadzen}`],
                ['p', seller.odznaka === 'tak' ? 'Ma odznakę' : 'Jeszcze bez odznaki'],
              ]) {
                const element = document.createElement(tag);
                element.textContent = text;
                box.append(element);
              }
              return box;
            })
            .addTo(this.map);
        }
        if (sellers.dane.length) {
          const points = sellers.dane.map((seller) =>
            L.latLng(seller.szerokosc_geograficzna, seller.dlugosc_geograficzna),
          );
          this.map.fitBounds(L.latLngBounds(points).pad(0.6), { maxZoom: 8 });
        }
      },
      error: (error) => this.error.set(aedErrorMessage(error)),
    });
  }

  ngOnDestroy(): void {
    this.map?.remove();
  }
}
