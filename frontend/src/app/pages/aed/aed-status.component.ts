import { Component, computed, input } from '@angular/core';

import { AedStatus } from './aed-api.service';
import { aedField } from './aed-schema';

/** Display names of the schema enum `status`. */
export const AED_STATUS_LABELS = aedField('status').etykiety as Record<AedStatus, string>;

export interface AedMark {
  box: [number, number];
  size: [number, number];
  anchor: [number, number];
  shape: string;
  glyph: string;
}

/**
 * The one set of status symbols: map markers, the map legend and the status label everywhere else.
 * A different outline and a different mark inside, so neither colour nor shape alone carries the status.
 * An active (confirmed) device is the only pin – the one to look for.
 */
export const AED_MARKS: Record<AedStatus, AedMark> = {
  aktywny: {
    box: [32, 42],
    size: [30, 39],
    anchor: [15, 38],
    shape: 'M16 40C16 40 3 26 3 16a13 13 0 0 1 26 0c0 10-13 24-13 24z',
    glyph: 'M10 16l4 4 8-8.5',
  },
  zgloszony: {
    box: [32, 32],
    size: [26, 26],
    anchor: [13, 13],
    shape: 'M7 4h18a3 3 0 0 1 3 3v18a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3z',
    glyph: 'M16 9.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 1 0 0-13zM16 12.5V16l2.5 1.5',
  },
  niepotwierdzony: {
    box: [32, 32],
    size: [28, 28],
    anchor: [14, 14],
    shape: 'M16 2.5L29.5 16 16 29.5 2.5 16z',
    glyph: 'M13 12.8a3 3 0 1 1 4.6 2.5c-1 .6-1.6 1.2-1.6 2.4M16 21.3v.2',
  },
  nieaktualny: {
    box: [32, 32],
    size: [28, 28],
    anchor: [14, 17],
    shape: 'M16 3.5L30 28.5H2z',
    glyph: 'M16 12v7.5M16 23.5v.2',
  },
  wycofany: {
    box: [32, 32],
    size: [26, 26],
    anchor: [13, 13],
    shape: 'M16 3a13 13 0 1 1 0 26 13 13 0 1 1 0-26z',
    glyph: 'M11 11l10 10M21 11L11 21',
  },
};

/** SVG markup of a status symbol, for Leaflet icons (styled by `.aed-mark--<status>`). */
export const aedMarkSvg = ({ box, size, shape, glyph }: AedMark) =>
  `<svg viewBox="0 0 ${box[0]} ${box[1]}" width="${size[0]}" height="${size[1]}" aria-hidden="true" focusable="false">` +
  `<path class="aed-mark__shape" d="${shape}"/><path class="aed-mark__glyph" d="${glyph}"/></svg>`;

/**
 * Status label: the map symbol of the status followed by its name, in the registry, on the QR page
 * and in the ministry panel. State is carried by the text and the shape; colour only repeats it.
 */
@Component({
  selector: 'app-aed-status',
  standalone: true,
  template: `
    <span class="aed-status">
      <span class="aed-mark aed-mark--{{ status() }}">
        <svg
          [attr.viewBox]="'0 0 ' + mark().box[0] + ' ' + mark().box[1]"
          [attr.width]="mark().size[0]"
          [attr.height]="mark().size[1]"
          aria-hidden="true"
          focusable="false">
          <path class="aed-mark__shape" [attr.d]="mark().shape" />
          <path class="aed-mark__glyph" [attr.d]="mark().glyph" />
        </svg>
      </span>
      <span class="aed-status__text">{{ labels[status()] }}</span>
    </span>
  `,
})
export class AedStatusComponent {
  readonly status = input.required<AedStatus>();
  protected readonly labels = AED_STATUS_LABELS;
  protected readonly mark = computed(() => AED_MARKS[this.status()]);
}
