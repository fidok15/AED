import { Component, computed, inject, input, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { catchError, map, of } from 'rxjs';

import { AedAccount, AedApiService, aedErrorMessage, aedFocusFactory } from './aed-api.service';
import { AED_DEMO_ACCOUNTS } from './aed-prototype';

/**
 * Sign-in to an AED demo account (POST /api/aed/sesja), shared by the company and the ministry panel.
 * A panel shows its content only when `allowed()` of this component's logic holds: see `aedHasRole`.
 */
@Component({
  selector: 'app-aed-login',
  standalone: true,
  imports: [FormsModule],
  template: `
    @if (error()) {
      <p class="aed-message aed-message--error" role="alert">{{ error() }}</p>
    }
    @if (!api.account()) {
      <form
        class="aed-panel aed-login"
        #form="ngForm"
        (ngSubmit)="form.valid && login(form.value.email, form.value.haslo)">
        <h2 class="aed-h2">{{ heading() }}</h2>
        <p class="aed-field__hint">
          Prototyp ma własne konta demonstracyjne. Nie podawaj tu hasła do portalu dane.gov.pl ani do innych usług.
        </p>
        <div class="aed-field">
          <label class="aed-field__label" for="aed-email">Adres e-mail konta</label>
          <input
            class="form-control"
            id="aed-email"
            name="email"
            type="email"
            autocomplete="username"
            required
            ngModel />
        </div>
        <div class="aed-field">
          <label class="aed-field__label" for="aed-haslo">Hasło</label>
          <input
            class="form-control"
            id="aed-haslo"
            name="haslo"
            type="password"
            autocomplete="current-password"
            required
            ngModel />
        </div>
        @if (form.submitted && form.invalid) {
          <p class="aed-field__error" role="alert">Podaj adres e-mail i hasło.</p>
        }
        <button class="btn btn-primary" type="submit">Zaloguj się</button>

        @if (demo().length) {
          <section class="aed-demo" aria-labelledby="aed-demo-heading">
            <h3 class="aed-h3" id="aed-demo-heading">Konta demonstracyjne</h3>
            <p class="aed-field__hint">
              Fikcyjne konta do wypróbowania prototypu. Wybierz „Wypełnij”, a potem „Zaloguj się”.
              @if (defaultPasswords() === false) {
                Na tym serwerze hasła kont demonstracyjnych są inne niż domyślne – przekazujemy je osobno.
              }
            </p>
            <ul class="aed-demo__list">
              @for (account of demo(); track account.email) {
                <li>
                  <span>
                    <strong>{{ account.opis }}</strong
                    ><br />
                    e-mail: {{ account.email }}<br />
                    @if (defaultPasswords() === false) {
                      hasło: przekazane osobno
                    } @else if (defaultPasswords()) {
                      hasło: {{ account.haslo }}
                    }
                  </span>
                  <button
                    class="btn btn-outline-primary"
                    type="button"
                    (click)="form.setValue({ email: account.email, haslo: defaultPasswords() ? account.haslo : '' })">
                    Wypełnij<span class="visually-hidden"> danymi konta: {{ account.opis }}</span>
                  </button>
                </li>
              }
            </ul>
          </section>
        }
      </form>
    } @else {
      <p class="aed-account" tabindex="-1">
        Zalogowano: <strong>{{ api.account().nazwa }}</strong>
        <button class="btn btn-link aed-account__out" type="button" (click)="logout()">Wyloguj się</button>
      </p>
      @if (wrongRole()) {
        <p class="aed-message aed-message--error">
          To konto nie ma dostępu do tego panelu. Wyloguj się i zaloguj na właściwe konto.
        </p>
      }
    }
  `,
})
export class AedLoginComponent {
  protected readonly api = inject(AedApiService);

  readonly rola = input.required<AedAccount['rola']>();
  readonly heading = input.required<string>();

  private readonly focus = aedFocusFactory();
  protected readonly error = signal('');
  protected readonly wrongRole = computed(() => this.api.account()?.rola !== this.rola());
  /** The service says whether the demo accounts still have the passwords shown on the cards (not on public servers). */
  protected readonly defaultPasswords = toSignal(
    this.api.stats().pipe(
      map((stats) => stats.hasla_demo_domyslne),
      catchError(() => of(undefined)),
    ),
  );
  protected readonly demo = computed(() => AED_DEMO_ACCOUNTS.filter((account) => account.rola === this.rola()));

  protected logout(): void {
    this.api.logout();
    this.focus('#aed-email');
  }

  protected login(email: string, haslo: string): void {
    this.api.login(email, haslo).subscribe({
      next: () => {
        this.error.set('');
        this.focus('.aed-account');
      },
      error: (error) => this.error.set(aedErrorMessage(error)),
    });
  }
}
