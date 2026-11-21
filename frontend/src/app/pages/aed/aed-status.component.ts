import { Component, input } from '@angular/core';

import { AedStatus } from './aed-api.service';

// Display names for the schema enum `status` (the schema keeps only the ASCII values).
export const AED_STATUS_LABELS: Record<AedStatus, string> = {
  aktywny: 'Aktywny',
  zgloszony: 'Zgłoszony',
  niepotwierdzony: 'Niepotwierdzony',
  nieaktualny: 'Nieaktualny',
  wycofany: 'Wycofany',
};

/**
 * Readiness indicator: the same mark in the registry and on the QR page, after the status window of a real AED.
 * State is carried by the icon shape and the text; colour only repeats it.
 */
@Component({
  selector: 'app-aed-status',
  standalone: true,
  template: `
    <span class="aed-status aed-status--{{ status() }}">
      <svg class="aed-status__window" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        @switch (status()) {
          @case ('aktywny') {
            <path d="M5.5 12.5l4.5 4.5 8.5-9.5" />
          }
          @case ('zgloszony') {
            <circle cx="12" cy="12" r="7.5" />
            <path d="M12 7.5V12l3 2" />
          }
          @case ('niepotwierdzony') {
            <path d="M8.8 9.3a3.2 3.2 0 1 1 5 2.6c-1 .7-1.8 1.3-1.8 2.6M12 18v.2" />
          }
          @case ('nieaktualny') {
            <path d="M12 5.5V14M12 18v.2" />
          }
          @case ('wycofany') {
            <path d="M7 7l10 10M17 7L7 17" />
          }
        }
      </svg>
      <span class="aed-status__text">{{ labels[status()] }}</span>
    </span>
  `,
})
export class AedStatusComponent {
  readonly status = input.required<AedStatus>();
  protected readonly labels = AED_STATUS_LABELS;
}
