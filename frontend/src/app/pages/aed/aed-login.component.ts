import { Component, computed, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { AedAccount, AedApiService, aedErrorMessage } from './aed-api.service';

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
      <form class="aed-panel aed-login" #form="ngForm" (ngSubmit)="form.valid && login(email.value, haslo.value)">
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
            ngModel
            #email />
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
            ngModel
            #haslo />
        </div>
        @if (form.submitted && form.invalid) {
          <p class="aed-field__error" role="alert">Podaj adres e-mail i hasło.</p>
        }
        <button class="btn btn-primary" type="submit">Zaloguj się</button>
      </form>
    } @else {
      <p class="aed-account">
        Zalogowano: <strong>{{ api.account().nazwa }}</strong>
        <button class="btn btn-link aed-account__out" type="button" (click)="api.logout()">Wyloguj się</button>
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

  protected readonly error = signal('');
  protected readonly wrongRole = computed(() => this.api.account()?.rola !== this.rola());

  protected login(email: string, haslo: string): void {
    this.api.login(email, haslo).subscribe({
      next: () => this.error.set(''),
      error: (error) => this.error.set(aedErrorMessage(error)),
    });
  }
}
