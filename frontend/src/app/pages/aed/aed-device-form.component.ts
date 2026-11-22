import { Component, inject, OnInit, signal } from '@angular/core';
import { FormGroup, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { LocalizeRouterPipe } from '@gilsdav/ngx-translate-router';

import { SeoService } from '@app/services/seo.service';
import { ScrollToFirstErrorDirective } from '@app/shared/forms/directives/scroll-to-first-error.directive';
import {
  AedAccepted,
  AedApiService,
  aedErrorMessage,
  aedFocusFactory,
  aedLinkFactory,
  AedProblem,
} from './aed-api.service';
import { AedFieldComponent } from './aed-field.component';
import { aedControl, aedGroups, aedRequired } from './aed-schema';

const CONDITION_FIELDS = ['stan_urzadzenia', 'data_stanu'];

/** Single-device form of a seller, generated from aed_standard/schema.json (profile `sprzedaz`). */
@Component({
  selector: 'app-aed-device-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, LocalizeRouterPipe, AedFieldComponent, ScrollToFirstErrorDirective],
  templateUrl: './aed-device-form.component.html',
})
export class AedDeviceFormComponent implements OnInit {
  private readonly api = inject(AedApiService);
  private readonly seo = inject(SeoService);

  private readonly required = aedRequired('sprzedaz');

  /** What the seller knows at the moment of sale, then what may already be known about the place. */
  protected readonly sale = aedGroups('sprzedawca');
  // The device's condition is the manager's own answer on the QR page; the service ignores it from a seller.
  protected readonly place = aedGroups('dysponent')
    .map((group) => ({ ...group, fields: group.fields.filter((f) => !CONDITION_FIELDS.includes(f.name)) }))
    .filter((group) => group.fields.length);
  protected readonly form = new FormGroup(
    Object.fromEntries(
      [...this.sale, ...this.place]
        .flatMap((group) => group.fields)
        .map((field) => [field.name, aedControl(field, this.required.includes(field.name))]),
    ),
  );

  private readonly focus = aedFocusFactory();
  protected readonly accepted = signal<AedAccepted | null>(null);
  protected readonly problems = signal<AedProblem[]>([]);
  protected readonly error = signal('');

  ngOnInit(): void {
    this.seo.setPageTitle(['Zgłoś urządzenie', 'Opiekun AED']);
  }

  protected readonly qrLink = aedLinkFactory();

  protected submit(): void {
    if (this.form.invalid) return; // appScrollToFirstError marks the fields and moves focus to the first one
    const filled = Object.entries(this.form.getRawValue()).filter(([, value]) => value !== null && value !== '');
    this.api.registerDevice(Object.fromEntries(filled)).subscribe({
      next: (report) => {
        this.accepted.set(report.przyjete[0] ?? null);
        if (report.przyjete.length) this.focus('#aed-done-heading');
        this.problems.set(report.problemy);
        this.error.set(
          report.przyjete.length || report.problemy.length
            ? ''
            : 'To urządzenie jest już w rejestrze (ten sam producent i numer seryjny).',
        );
      },
      error: (error) => this.error.set(aedErrorMessage(error)),
    });
  }

  protected another(): void {
    this.form.reset();
    this.accepted.set(null);
  }
}
