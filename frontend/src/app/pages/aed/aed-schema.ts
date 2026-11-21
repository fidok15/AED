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
  przyklad?: string;
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

// The schema does not say yet who fills a field (system, seller, site manager) and has no display
// names for groups. Until it does, that split lives only here.
export const AED_GROUP_TITLES: Record<string, string> = {
  urzadzenie: 'Urządzenie',
  odpowiedzialnosc: 'Dysponent, czyli kto odpowiada za urządzenie',
  polozenie: 'Położenie',
  dostep: 'Dostęp',
};

/** Fields of a group that a person fills in; `wprowadzajacy_*` comes from the logged-in account. */
export const aedGroupFields = (grupa: string): AedField[] =>
  AED_FIELDS.filter((field) => field.grupa === grupa && !field.name.startsWith('wprowadzajacy_'));

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
