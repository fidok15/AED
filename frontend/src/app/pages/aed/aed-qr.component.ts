import { NgTemplateOutlet } from '@angular/common';
import { Component, computed, inject, input, OnInit, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';

import { SeoService } from '@app/services/seo.service';
import { ScrollToFirstErrorDirective } from '@app/shared/forms/directives/scroll-to-first-error.directive';
import {
  AedApiService,
  AedCondition,
  aedErrorMessage,
  aedFocusFactory,
  AedRecord,
  AedSignalType,
} from './aed-api.service';
import { AedFieldComponent } from './aed-field.component';
import { AedHoursPickerComponent } from './aed-hours-picker.component';
import { aedControl, aedField, aedRequired, aedRequiredForStatus } from './aed-schema';
import { AED_STATUS_LABELS, AedStatusComponent } from './aed-status.component';

/** As in the service: a reminder goes out this many days before the battery or the electrodes expire. */
const EXPIRY_NOTICE_DAYS = 60;
/** Validator codes of missing values; as in the service, they do not block a problem report. */
const ODBL = 'ODbL 1.0';
const REQUIRED_CODES = ['brak_wymaganego', 'wymagane_dla_aktywnego'];

/**
 * Phone screen opened from the QR sticker: /aed/qr/{id_aed}.
 * With `?t=<token>` the site manager completes and confirms the record; without it anyone can only
 * send a signal to the device owner, which never edits the data (CLAUDE.md, hard rule 2).
 */
@Component({
  selector: 'app-aed-qr',
  standalone: true,
  imports: [
    NgTemplateOutlet,
    ReactiveFormsModule,
    AedFieldComponent,
    AedHoursPickerComponent,
    AedStatusComponent,
    ScrollToFirstErrorDirective,
  ],
  templateUrl: './aed-qr.component.html',
})
export class AedQrComponent implements OnInit {
  private readonly api = inject(AedApiService);
  private readonly seo = inject(SeoService);
  private readonly focus = aedFocusFactory();

  /** Route parameter and query parameter, bound by the router. */
  readonly id = input<string>();
  readonly t = input<string>();

  protected readonly record = signal<AedRecord | null>(null);
  protected readonly loadError = signal('');
  /** The manager link is unknown or expired (403): the device exists, only the link does not work. */
  protected readonly badLink = signal(false);
  /** Same page without the token: the public view with the bystander's signal (full reload, so it loads anew). */
  protected readonly publicPage = () => location.pathname;
  protected readonly sendError = signal('');
  /** Result screen: readiness confirmed, a problem reported by the manager, or a bystander's signal sent. */
  protected readonly done = signal<'potwierdzenie' | 'problem' | 'sygnal' | null>(null);

  protected readonly statusLabels = AED_STATUS_LABELS;
  protected readonly locating = signal(false);
  protected readonly located = signal('');
  protected readonly locationError = signal('');

  // Manager: fields of the confirmation request, in the order of the three steps.
  // Required: what publication needs plus what the schema demands for status `aktywny`.
  private readonly required = [...aedRequired('publikacja'), ...aedRequiredForStatus('aktywny')];
  protected readonly coordinates = ['szerokosc_geograficzna', 'dlugosc_geograficzna'].map(aedField);
  protected readonly place = ['nazwa', 'miejscowosc', 'nazwa_ulicy', 'nr_budynku', 'kod_pocztowy'].map(aedField);
  protected readonly spot = ['opis_lokalizacji', 'wewnatrz_budynku'].map(aedField);
  protected readonly access = aedField('dostep');
  protected readonly hours = aedField('godziny_dostepu');
  protected readonly hoursNote = aedField('godziny_dostepu_opis');
  /** Optional step: after replacing the battery or the electrodes the manager enters the new expiry date. */
  protected readonly expiry = ['data_waznosci_baterii', 'data_waznosci_elektrod'].map(aedField);
  /** Expiry dates that have passed or pass within the reminder window; then the step moves to the top. */
  protected readonly expiring = computed(() => {
    const limit = new Date(Date.now() + EXPIRY_NOTICE_DAYS * 86_400_000).toISOString().slice(0, 10);
    return this.expiry.filter((field) => {
      const date = String(this.record()?.[field.name] ?? '');
      return date !== '' && date <= limit;
    });
  });
  protected readonly values = new FormGroup(
    Object.fromEntries(
      [...this.coordinates, ...this.place, ...this.spot, this.access, this.hours, this.hoursNote, ...this.expiry].map(
        (field) => [field.name, aedControl(field, this.required.includes(field.name))],
      ),
    ),
  );
  /**
   * A point known only from OpenStreetMap (ODbL): the form starts empty and the manager gives every value,
   * so the published record is the owner's own data (CLAUDE.md, hard rule 3). The service starts from an empty
   * record too and then also takes the owner's contact.
   */
  protected readonly takeover = computed(() => this.record()?.['licencja'] === ODBL);
  /** The manager may add the contact on a takeover and whenever the record has none yet (e.g. a city dataset). */
  protected readonly needsContact = computed(() => this.takeover() || !this.record()?.['dysponent_email']);
  protected readonly ownerFields = ['dysponent_nazwa', 'dysponent_email', 'dysponent_telefon'].map(aedField);
  protected readonly owner = new FormGroup(
    Object.fromEntries(this.ownerFields.map((field) => [field.name, aedControl(field)])),
  );
  protected readonly stan = new FormControl<AedCondition | null>(null, Validators.required);
  protected readonly uwagi = new FormControl('');
  protected readonly form = new FormGroup({
    values: this.values,
    owner: this.owner,
    stan: this.stan,
    uwagi: this.uwagi,
  });

  // Anyone: the public signal.
  protected readonly signalTypes: { typ: AedSignalType; label: string }[] = [
    { typ: 'jest', label: 'Urządzenie jest na miejscu' },
    { typ: 'brak', label: 'Nie ma tu urządzenia' },
    { typ: 'uszkodzony', label: 'Urządzenie jest uszkodzone' },
    { typ: 'zamkniety', label: 'Miejsce jest zamknięte lub niedostępne' },
  ];
  protected readonly signalForm = new FormGroup({
    typ: new FormControl<AedSignalType | null>(null, Validators.required),
    uwagi: new FormControl(''),
  });
  private signalPosition: { szerokosc_geograficzna: number; dlugosc_geograficzna: number } | null = null;

  ngOnInit(): void {
    this.seo.setPageTitle([this.t() ? 'Potwierdź dane defibrylatora' : 'Defibrylator AED', 'Rejestr AED']);

    this.stan.valueChanges.subscribe((stan) => {
      this.uwagi.setValidators(stan === 'problem' ? Validators.required : null);
      this.uwagi.updateValueAndValidity();
    });

    this.api.device(this.id(), this.t()).subscribe({
      next: (record) => {
        this.record.set(record);
        if (!this.takeover()) this.values.patchValue(record);
      },
      error: (error) => {
        this.badLink.set(error.status === 403);
        this.loadError.set(aedErrorMessage(error));
      },
    });
  }

  /** One tap: read the phone position and put it into the form (manager) or attach it to the signal. */
  protected locate(): void {
    if (this.locating()) return;
    this.locationError.set('');
    if (!navigator.geolocation) {
      this.locationError.set('Ta przeglądarka nie udostępnia lokalizacji. Wpisz współrzędne ręcznie.');
      return;
    }
    this.locating.set(true);
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const position = {
          szerokosc_geograficzna: +coords.latitude.toFixed(6),
          dlugosc_geograficzna: +coords.longitude.toFixed(6),
        };
        this.values.patchValue(position);
        this.signalPosition = position;
        const accuracy = Math.round(coords.accuracy);
        this.located.set(
          `Zapisano położenie: ${position.szerokosc_geograficzna}, ${position.dlugosc_geograficzna} ` +
            `(dokładność około ${accuracy} m).` +
            (accuracy > 50
              ? ' To mało dokładny odczyt. Podejdź do okna albo wyjdź na zewnątrz i spróbuj ponownie, albo popraw współrzędne ręcznie.'
              : ''),
        );
        this.locating.set(false);
      },
      (error) => {
        this.locationError.set(
          error.code === error.PERMISSION_DENIED
            ? 'Przeglądarka nie ma zgody na lokalizację. Zezwól na nią w ustawieniach albo wpisz współrzędne ręcznie.'
            : 'Nie udało się ustalić położenia. Wyjdź na otwartą przestrzeń i spróbuj ponownie albo wpisz współrzędne ręcznie.',
        );
        this.locating.set(false);
      },
      { enableHighAccuracy: true, timeout: 15000 },
    );
  }

  protected confirm(): void {
    if (this.form.invalid) return; // appScrollToFirstError marks the fields and moves focus to the first one
    // The service changes only the fields it receives. A field the manager emptied is therefore sent as '',
    // otherwise the old text would stay in the record; untouched empty fields are left out.
    const controls = { ...this.values.controls, ...(this.needsContact() ? this.owner.controls : {}) };
    const sent = Object.entries(controls)
      .filter(([, control]) => control.dirty || (control.value !== null && control.value !== ''))
      .map(([name, control]) => [name, control.value ?? '']);
    const body = {
      ...Object.fromEntries(sent),
      t: this.t(),
      stan: this.stan.value,
      uwagi: this.uwagi.value || undefined,
    };
    this.api.confirm(this.id(), body).subscribe({
      next: (record) => {
        this.record.set(record);
        // The service decides: only a device reported as ready becomes `aktywny`.
        this.finish(record.status === 'aktywny' ? 'potwierdzenie' : 'problem');
      },
      // A problem report may be incomplete: the service lists missing fields too, but only wrong values block it.
      error: (error) =>
        this.sendError.set(
          aedErrorMessage(error, (problem) => body.stan !== 'problem' || !REQUIRED_CODES.includes(problem.kod)),
        ),
    });
  }

  protected sendSignal(): void {
    if (this.signalForm.invalid) return;
    const { typ, uwagi } = this.signalForm.getRawValue();
    this.api.signal(this.id(), { typ, uwagi: uwagi || undefined, ...this.signalPosition }).subscribe({
      next: () => this.finish('sygnal'),
      error: (error) => this.sendError.set(aedErrorMessage(error)),
    });
  }

  /** Show the result screen and move focus to its heading, so screen readers announce it. */
  private finish(done: 'potwierdzenie' | 'problem' | 'sygnal'): void {
    this.sendError.set('');
    this.done.set(done);
    this.focus('#aed-done');
  }
}
