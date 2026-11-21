import { FormControl, ValidatorFn, Validators } from '@angular/forms';

// Single source of truth for the AED data structure (CLAUDE.md, hard rule 1).
// Imported straight from the repository root, so nothing is copied into the fork.
import schema from '../../../../../aed_standard/schema.json';

export interface AedField {
  name: string;
  title: string;
  description: string;
  type: string;
  format?: string;
  grupa: string;
  /** Who fills the field in: sprzedawca, dysponent or system. */
  wypelnia: string;
  przyklad?: string;
  /** Display labels of enum values. */
  etykiety?: Record<string, string>;
  constraints?: { enum?: string[]; pattern?: string; minimum?: number; maximum?: number };
}

export type AedProfile = keyof typeof schema.profile_wymagalnosci;
export type AedValue = string | number | null;

export const AED_FIELDS: AedField[] = schema.fields;

export const aedField = (name: string): AedField => AED_FIELDS.find((field) => field.name === name);

export const aedRequired = (profile: AedProfile): string[] => schema.profile_wymagalnosci[profile].wymagane;

/** Choices of a field: its enum, or tak/nie for a boolean. */
export const aedOptions = (field: AedField): string[] =>
  field.constraints?.enum ??
  (field.type === 'boolean' ? [schema.wartosci_logiczne.prawda, schema.wartosci_logiczne.falsz] : []);

/** Display label of an enum value (`etykiety` in the schema); other values are shown as they are. */
export const aedLabel = (field: AedField, value: AedValue | undefined): string =>
  field.etykiety?.[String(value)] ?? String(value ?? '');

/** Fields required before a record may get the given status, e.g. `aktywny`. */
export const aedRequiredForStatus = (status: keyof typeof schema.wymagane_dla_statusu): string[] =>
  schema.wymagane_dla_statusu[status];

/** Form sections for one role: the schema groups that hold fields this role fills in (`wypelnia`). */
export const aedGroups = (wypelnia: 'sprzedawca' | 'dysponent'): { title: string; fields: AedField[] }[] =>
  Object.entries(schema.grupy)
    .map(([grupa, title]) => ({
      title,
      fields: AED_FIELDS.filter((field) => field.grupa === grupa && field.wypelnia === wypelnia),
    }))
    .filter((group) => group.fields.length);

/** Form control validated against the schema constraints of its field. */
export function aedControl(field: AedField, required = false): FormControl<AedValue> {
  const fitsSchema: ValidatorFn = (control) => {
    const message = aedValueError(field, control.value);
    return message ? { aed: message } : null;
  };
  return new FormControl<AedValue>(null, required ? [Validators.required, fitsSchema] : [fitsSchema]);
}

/** Polish message for a single value, or '' when the value fits the schema. Shared by the form and the CSV preview. */
export function aedValueError(field: AedField, value: AedValue): string {
  const text = String(value ?? '').trim();
  const { pattern, minimum, maximum, enum: options } = field.constraints ?? {};
  if (!text) return '';
  if (field.type === 'date' && !/^\d{4}-\d{2}-\d{2}$/.test(text)) return 'Podaj datę w formacie RRRR-MM-DD.';
  if (options && !options.includes(text)) return `Wybierz jedną z wartości: ${options.join(', ')}.`;
  if (pattern && !new RegExp(pattern).test(text)) return `Popraw format. Przykład: ${field.przyklad}.`;
  if (field.format === 'email' && !/^\S+@\S+\.\S+$/.test(text)) return 'Podaj poprawny adres e-mail.';
  if (field.type === 'number' || field.type === 'integer') {
    const n = Number(text);
    if (Number.isNaN(n)) return 'Podaj liczbę z kropką dziesiętną.';
    if ((minimum != null && n < minimum) || (maximum != null && n > maximum)) {
      return `Podaj liczbę od ${minimum} do ${maximum}.`;
    }
  }
  return '';
}
