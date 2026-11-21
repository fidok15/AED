import { Component, input } from '@angular/core';

import { AedStatus } from './aed-api.service';
import { aedField } from './aed-schema';

/** Display names of the schema enum `status`. */
export const AED_STATUS_LABELS = aedField('status').etykiety as Record<AedStatus, string>;

/** Mark drawn in the status window (24×24 viewBox): a different shape for every status. */
export const AED_STATUS_PATHS: Record<AedStatus, string> = {
  aktywny: 'M5.5 12.5l4.5 4.5 8.5-9.5',
  zgloszony: 'M12 4.5a7.5 7.5 0 1 0 0 15 7.5 7.5 0 1 0 0-15zM12 7.5V12l3 2',
  niepotwierdzony: 'M8.8 9.3a3.2 3.2 0 1 1 5 2.6c-1 .7-1.8 1.3-1.8 2.6M12 18v.2',
  nieaktualny: 'M12 5.5V14M12 18v.2',
  wycofany: 'M7 7l10 10M17 7L7 17',
};

/**
 * Readiness indicator: the same mark in the registry, on the map and on the QR page, after the status
 * window of a real AED. State is carried by the shape of the mark and by the text; colour only repeats it.
 */
@Component({
  selector: 'app-aed-status',
  standalone: true,
  template: `
    <span class="aed-status aed-status--{{ status() }}">
      <svg class="aed-status__window" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path [attr.d]="paths[status()]" />
      </svg>
      <span class="aed-status__text">{{ labels[status()] }}</span>
    </span>
  `,
})
export class AedStatusComponent {
  readonly status = input.required<AedStatus>();
  protected readonly labels = AED_STATUS_LABELS;
  protected readonly paths = AED_STATUS_PATHS;
}
