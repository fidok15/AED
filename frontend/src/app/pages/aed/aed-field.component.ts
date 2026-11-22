import { Component, computed, input } from '@angular/core';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';

import { AED_MONTH_DATE_HINT, AedField, aedLabel, aedOptions, AedValue } from './aed-schema';

/**
 * One form field generated from aed_standard/schema.json: label from `title`, help from `description`,
 * example from `przyklad`, choices from the enum. Used by the seller form and by the QR page.
 */
@Component({
  selector: 'app-aed-field',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './aed-field.component.html',
})
export class AedFieldComponent {
  readonly field = input.required<AedField>();
  readonly control = input.required<FormControl<AedValue>>();

  protected readonly id = computed(() => 'aed-' + this.field().name);
  protected readonly options = computed(() => aedOptions(this.field()));
  /** RRRR-MM-DD or RRRR-MM: one text box (a date picker cannot take a month only). */
  protected readonly monthDate = computed(() => !!this.field().dokladnosc_daty);
  protected readonly monthDateHint = AED_MONTH_DATE_HINT;
  protected readonly inputType = computed(() => {
    const { type, format } = this.field();
    if (type === 'date') return 'date';
    if (type === 'number' || type === 'integer') return 'number';
    return format === 'email' ? 'email' : 'text';
  });

  protected readonly label = (option: string) => aedLabel(this.field(), option);

  protected get required(): boolean {
    return this.control().hasValidator(Validators.required);
  }

  protected get invalid(): boolean {
    return this.control().touched && this.control().invalid;
  }

  protected get error(): string {
    return this.control().errors?.['aed'] ?? 'Uzupełnij to pole.';
  }
}
