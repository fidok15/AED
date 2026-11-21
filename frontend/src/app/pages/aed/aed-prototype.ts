import { Component, inject } from '@angular/core';
import { CanActivateFn, Router, RouterLink } from '@angular/router';
import { environment } from '@env/environment';
import { LocalizeRouterPipe, LocalizeRouterService } from '@gilsdav/ngx-translate-router';

import { SeoService } from '@app/services/seo.service';

/**
 * Prototype mode: every build except the portal's own production build.
 * The prototype runs on a public address under the portal's gov.pl header and talks to the production
 * portal API, so it must say what it is and must not take portal credentials.
 */
export const AED_PROTOTYPE = !environment.production;

/** In prototype mode the portal's own entry notices (RODO modal) stay away from the AED pages. */
export const aedSkipsPortalNotice = (path: string): boolean => AED_PROTOTYPE && /\/aed(\/|$)/.test(path);

export interface AedDemoAccount {
  rola: 'firma' | 'ministerstwo';
  opis: string;
  email: string;
  haslo: string;
}

/**
 * Demo accounts of aed_service (fictional data), shown on the sign-in cards so the jury can walk the
 * whole path. They live in the environment files of the prototype builds (environment.ts,
 * environment.aed.ts); the production environment has none, so a production bundle does not contain them.
 */
export const AED_DEMO_ACCOUNTS: AedDemoAccount[] =
  (environment as { aedDemoAccounts?: AedDemoAccount[] }).aedDemoAccounts ?? [];

/** Strip shown above everything on every page, the phone screen from a QR sticker included. */
@Component({
  selector: 'app-aed-prototype-banner',
  standalone: true,
  template: `
    @if (prototype) {
      <aside class="banner" lang="pl" aria-label="Informacja o prototypie">
        <svg class="banner__icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
          <path d="M12 3 22 20H2z" />
          <path d="M12 10v4.5M12 17.2v.3" />
        </svg>
        <p class="banner__text">
          Prototyp hackathonowy HackNation 2026 – to nie jest serwis dane.gov.pl. Dane demonstracyjne.
        </p>
      </aside>
    }
  `,
  styles: `
    .banner {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.625rem;
      padding: 0.5rem 1rem;
      border-bottom: 2px solid #1b1b1b;
      background: #ffc605;
      color: #1b1b1b;
    }

    .banner__icon {
      flex: none;
      width: 1.5rem;
      height: 1.5rem;
      fill: none;
      stroke: currentColor;
      stroke-width: 2;
      stroke-linecap: round;
      stroke-linejoin: round;
    }

    .banner__text {
      margin: 0;
      font-size: 0.9375rem;
      font-weight: 700;
      line-height: 1.4;
    }

    @media (max-width: 575.98px) {
      .banner {
        padding: 0.375rem 0.75rem;
      }

      .banner__icon {
        display: none;
      }

      .banner__text {
        font-size: 0.8125rem;
      }
    }
  `,
})
export class AedPrototypeBannerComponent {
  protected readonly prototype = AED_PROTOTYPE;
}

/** Guard for the portal's `!user` routes: in prototype mode nobody reaches the portal sign-in or sign-up forms. */
export const aedPortalAccountsOff: CanActivateFn = () =>
  !AED_PROTOTYPE ||
  inject(Router).parseUrl(inject(LocalizeRouterService).translateRoute('/!aed/!portal-accounts') as string);

/** Where the guard above sends the visitor. */
@Component({
  selector: 'app-aed-portal-accounts-off',
  standalone: true,
  imports: [RouterLink, LocalizeRouterPipe],
  template: `
    <h1 class="heading heading--md">Logowanie do portalu jest tu wyłączone</h1>
    <p class="aed-lede">
      To prototyp, a nie serwis dane.gov.pl. Nie można się tu zalogować ani zarejestrować kontem portalu i nie należy
      podawać tu jego hasła.
    </p>
    <p>Prototyp ma własne konta demonstracyjne z fikcyjnymi danymi:</p>
    <ul>
      <li><a [routerLink]="['/!aed', '!company'] | localize">Panel firmy – producent lub sprzedawca AED</a></li>
      <li><a [routerLink]="['/!aed', '!ministry'] | localize">Panel ministerstwa</a></li>
    </ul>
    <p>
      Konto w prawdziwym portalu założysz na stronie
      <a href="https://dane.gov.pl">dane.gov.pl</a>.
    </p>
  `,
})
export class AedPortalAccountsOffComponent {
  constructor() {
    inject(SeoService).setPageTitle('Logowanie do portalu wyłączone w prototypie');
  }
}
