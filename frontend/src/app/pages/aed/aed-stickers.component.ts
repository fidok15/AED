import { Component, computed, inject, input, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LocalizeRouterPipe } from '@gilsdav/ngx-translate-router';

import { SeoService } from '@app/services/seo.service';
import { AedApiService, aedErrorMessage, AedSubmission } from './aed-api.service';

/**
 * Printable sheet of QR stickers for the devices a company has reported: 3 across on A4.
 * `?zgloszenie=<id>` narrows the sheet to one submission; without it every accepted device is listed.
 */
@Component({
  selector: 'app-aed-stickers',
  standalone: true,
  imports: [RouterLink, LocalizeRouterPipe],
  template: `
    <div class="aed-stickers">
      <div class="aed-stickers__screen">
        <p class="aed-back"><a [routerLink]="['/!aed', '!company'] | localize">Wróć do panelu firmy</a></p>
        <h1 class="heading heading--md">Naklejki z kodem QR do wydruku</h1>
        <p class="aed-lede">
          Arkusz A4, trzy naklejki w rzędzie. Wydrukuj w skali 100%, rozetnij i przyklej każdą naklejkę na urządzeniu
          albo na jego szafce.
        </p>
        @if (error()) {
          <p class="aed-message aed-message--error" role="alert">{{ error() }}</p>
        }
        @if (devices().length) {
          <p>
            <button class="btn btn-primary" type="button" (click)="print()">
              Drukuj naklejki ({{ devices().length }})
            </button>
          </p>
        } @else if (loaded()) {
          <p class="aed-message">
            Nie ma jeszcze naklejek do wydruku. Pojawią się po zgłoszeniu urządzeń w panelu firmy.
          </p>
        }
      </div>

      <ul class="aed-stickers__sheet">
        @for (device of devices(); track device.id_aed) {
          <li class="aed-sticker">
            <img [src]="device.naklejka_url" alt="Naklejka z kodem QR urządzenia {{ device.id_aed }}" />
            <p class="aed-sticker__id">{{ device.id_aed }}</p>
            <p class="aed-sticker__for">{{ device.producent }} {{ device.model }}, nr {{ device.numer_seryjny }}</p>
            <p class="aed-sticker__how">
              Przyklej w widocznym miejscu na urządzeniu lub szafce. Dysponent skanuje kod i potwierdza miejsce.
            </p>
          </li>
        }
      </ul>
    </div>
  `,
})
export class AedStickersComponent implements OnInit {
  private readonly api = inject(AedApiService);
  private readonly seo = inject(SeoService);

  /** Query parameter, bound by the router. */
  readonly zgloszenie = input<string>();

  protected readonly error = signal('');
  protected readonly loaded = signal(false);
  private readonly submissions = signal<AedSubmission[]>([]);
  protected readonly devices = computed(() =>
    this.submissions()
      .filter((submission) => !this.zgloszenie() || String(submission.id) === this.zgloszenie())
      .flatMap((submission) => submission.przyjete),
  );

  ngOnInit(): void {
    this.seo.setPageTitle(['Naklejki QR do wydruku', 'Opiekun AED']);
    this.api.submissions().subscribe({
      next: (submissions) => {
        this.submissions.set(submissions);
        this.loaded.set(true);
      },
      error: (error) => this.error.set(aedErrorMessage(error)),
    });
  }

  protected print(): void {
    window.print();
  }
}
