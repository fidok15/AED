import { Component, inject, OnInit, signal } from '@angular/core';
import { RouterLink, UrlTree } from '@angular/router';
import { LocalizeRouterPipe } from '@gilsdav/ngx-translate-router';

import { SeoService } from '@app/services/seo.service';
import { AedApiService, aedLinkFactory } from './aed-api.service';

/**
 * Landing page of the AED area: three paths through the process, in the order they happen,
 * and the data itself. It stands in for a manual, so each item says what to look at.
 */
@Component({
  selector: 'app-aed-home',
  standalone: true,
  imports: [RouterLink, LocalizeRouterPipe],
  template: `
    <h1 class="heading heading--md">Jeden rejestr defibrylatorów AED dla Polski</h1>
    <p class="aed-lede">
      Firma zgłasza sprzedane urządzenie, jego dysponent potwierdza miejsce z naklejki z kodem QR, a ministerstwo
      prowadzi rejestr i publikuje zbiór na dane.gov.pl.
    </p>
    <p>
      <a class="btn btn-primary" [routerLink]="['/!aed', '!registry'] | localize" fragment="aed-near">
        Znajdź najbliższy AED
      </a>
    </p>

    <h2 class="aed-h2">Jak urządzenie trafia do rejestru</h2>
    <p>Przejdź te trzy kroki po kolei.</p>
    <ol class="aed-paths">
      <li class="aed-path">
        <h3 class="aed-path__title">
          <a [routerLink]="['/!aed', '!company'] | localize">Firma zgłasza urządzenia</a>
        </h3>
        <p>
          Zaloguj się kontem demonstracyjnym, pobierz przykładowy plik CSV i wgraj go. Zwróć uwagę na raport sprawdzenia
          pliku, a po wysłaniu – na naklejki z kodem QR i linki dla dysponentów.
        </p>
      </li>
      <li class="aed-path">
        <h3 class="aed-path__title">Dysponent potwierdza dane urządzenia po zeskanowaniu naklejki</h3>
        <p>
          Otwórz „Stronę potwierdzenia dla dysponenta” z wyniku zgłoszenia w kroku 1 albo link z wiadomości w panelu
          ministerstwa – najlepiej na telefonie. Zwróć uwagę na lokalizację jednym przyciskiem i wybór godzin dostępu.
        </p>
        @if (publicQr(); as link) {
          <p>
            Sam kod z naklejki nie daje prawa zmiany danych:
            <a [routerLink]="link">zobacz, co widzi osoba, która tylko zeskanowała kod</a>.
          </p>
        }
      </li>
      <li class="aed-path">
        <h3 class="aed-path__title">
          <a [routerLink]="['/!aed', '!ministry'] | localize">Ministerstwo prowadzi rejestr i publikuje zbiór</a>
        </h3>
        <p>
          Zaloguj się kontem demonstracyjnym ministerstwa. Zwróć uwagę na kolejkę możliwych duplikatów, wiadomości do
          dysponentów, historię zadań cyklicznych i plik do publikacji.
        </p>
      </li>
    </ol>

    <section class="aed-data" aria-labelledby="aed-data-heading">
      <h2 class="aed-h2" id="aed-data-heading">Dane i standard</h2>
      <ul>
        <li>
          <a [routerLink]="['/!aed', '!registry'] | localize">Rejestr urządzeń z listą i mapą</a> – dane z sześciu
          otwartych źródeł w jednej strukturze, ze statusem i kompletnością każdego rekordu.
        </li>
        <li>
          <a [routerLink]="['/!aed', '!sellers'] | localize">Ranking firm</a> – kto zgłasza urządzenia i dba o ich dane,
          z odznaką za wynik.
        </li>
        <li>
          <a [routerLink]="['/!aed', '!konwerter'] | localize">Konwerter do standardu AED</a> – zamień własny plik z
          defibrylatorami na wykaz gotowy do publikacji na dane.gov.pl, bez logowania.
        </li>
        <li>
          <a [href]="api.exportUrl" download>Zbiór do publikacji na dane.gov.pl (CSV)</a> – tylko rekordy gotowe do
          publikacji, w kolumnach standardu.
        </li>
      </ul>
    </section>
  `,
})
export class AedHomeComponent implements OnInit {
  protected readonly api = inject(AedApiService);
  private readonly seo = inject(SeoService);
  private readonly link = aedLinkFactory();

  /** Sticker address of a device that still waits for its manager; found without signing in. */
  protected readonly publicQr = signal<UrlTree | null>(null);

  ngOnInit(): void {
    this.seo.setPageTitle('Rejestr AED');
    this.api.devices({ status: 'zgloszony', na_stronie: 1 }).subscribe({
      next: (page) => this.publicQr.set(page.dane[0] ? this.link(`/aed/qr/${page.dane[0].id_aed}`) : null),
      error: () => this.publicQr.set(null),
    });
  }
}
