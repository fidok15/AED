import { Component, input, OnInit, signal } from '@angular/core';
import { FormControl } from '@angular/forms';

import { aedHoursFromRows, AedHoursRow, aedHoursRows, aedRowsFromHours } from './aed-hours';
import { AedField, AedValue } from './aed-schema';

const ALWAYS = '24/7';

/**
 * Access hours without typing the opening_hours syntax: round the clock, or chosen days with times.
 * Writes the syntax into the `godziny_dostepu` control. An existing value the picker cannot show
 * (for example with public holidays) can be kept as it is.
 */
@Component({
  selector: 'app-aed-hours-picker',
  standalone: true,
  template: `
    @let invalid = control().touched && control().invalid;
    <fieldset
      class="aed-field form-field"
      [class.is-invalid]="invalid"
      [attr.aria-describedby]="invalid ? 'aed-hours-error' : null">
      <legend class="aed-field__label">{{ field().title }} <span class="aed-field__required">(wymagane)</span></legend>
      <div class="aed-choices">
        <label class="aed-choice">
          <input type="radio" name="aed-hours-mode" value="all" [checked]="mode() === 'all'" (change)="choose('all')" />
          <span>Całą dobę, we wszystkie dni</span>
        </label>
        <label class="aed-choice">
          <input
            type="radio"
            name="aed-hours-mode"
            value="rows"
            [checked]="mode() === 'rows'"
            (change)="choose('rows')" />
          <span>W wybranych dniach i godzinach</span>
        </label>
        @if (original) {
          <label class="aed-choice">
            <input
              type="radio"
              name="aed-hours-mode"
              value="keep"
              [checked]="mode() === 'keep'"
              (change)="choose('keep')" />
            <span>Bez zmian: {{ original }}</span>
          </label>
        }
      </div>

      @if (mode() === 'rows') {
        <div class="aed-hours">
          @for (row of rows; track row.days) {
            <div class="aed-hours__row" role="group" [attr.aria-label]="row.label">
              <label class="aed-hours__day">
                <input
                  type="checkbox"
                  [checked]="row.open"
                  (change)="row.open = $any($event.target).checked; write()" />
                <span>{{ row.label }}</span>
              </label>
              @if (row.open) {
                <label class="aed-hours__time">
                  <span>od</span>
                  <input
                    class="form-control"
                    type="time"
                    [value]="row.from"
                    [attr.aria-label]="row.label + ', dostęp od godziny'"
                    (input)="row.from = $any($event.target).value; write()" />
                </label>
                <label class="aed-hours__time">
                  <span>do</span>
                  <input
                    class="form-control"
                    type="time"
                    [value]="row.to"
                    [attr.aria-label]="row.label + ', dostęp do godziny'"
                    (input)="row.to = $any($event.target).value; write()" />
                </label>
              }
            </div>
          }
        </div>
      }

      @if (invalid) {
        <p class="aed-field__error" id="aed-hours-error">
          <span class="visually-hidden">Błąd: </span>
          {{
            mode() === 'rows'
              ? 'Zaznacz co najmniej jeden dzień. Godzina „od” musi być wcześniejsza niż „do”.'
              : 'Wybierz jedną z opcji.'
          }}
        </p>
      }
    </fieldset>
  `,
})
export class AedHoursPickerComponent implements OnInit {
  readonly field = input.required<AedField>();
  readonly control = input.required<FormControl<AedValue>>();

  protected readonly mode = signal<'all' | 'rows' | 'keep' | null>(null);
  protected rows: AedHoursRow[] = aedHoursRows();
  /** Value found in the record that the picker cannot show as rows. */
  protected original = '';

  ngOnInit(): void {
    const value = String(this.control().value ?? '').trim();
    const rows = value && value !== ALWAYS ? aedRowsFromHours(value) : null;
    if (rows) this.rows = rows;
    else if (value && value !== ALWAYS) this.original = value;
    this.mode.set(!value ? null : value === ALWAYS ? 'all' : rows ? 'rows' : 'keep');
  }

  protected choose(mode: 'all' | 'rows' | 'keep'): void {
    this.mode.set(mode);
    this.write();
  }

  protected write(): void {
    const mode = this.mode();
    this.control().setValue(mode === 'all' ? ALWAYS : mode === 'rows' ? aedHoursFromRows(this.rows) : this.original);
    this.control().markAsDirty();
  }
}
