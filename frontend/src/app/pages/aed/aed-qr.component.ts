import { afterNextRender, Component, ElementRef, inject, Injector, input, OnInit, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';

import { SeoService } from '@app/services/seo.service';
import { ScrollToFirstErrorDirective } from '@app/shared/forms/directives/scroll-to-first-error.directive';
import { AedApiService, AedCondition, aedErrorMessage, AedRecord, AedSignalType } from './aed-api.service';
import { AedFieldComponent } from './aed-field.component';
import { AedHoursPickerComponent } from './aed-hours-picker.component';
import { aedControl, aedField, aedRequired, aedRequiredForStatus } from './aed-schema';
import { AedStatusComponent } from './aed-status.component';

/**
 * Phone screen opened from the QR sticker: /aed/qr/{id_aed}.
 * With `?t=<token>` the site manager completes and confirms the record; without it anyone can only
 * send a signal to the device owner, which never edits the data (CLAUDE.md, hard rule 2).
 */
@Component({
  selector: 'app-aed-qr',
  standalone: true,
  imports: [
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
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly injector = inject(Injector);

  /** Route parameter and query parameter, bound by the router. */
  readonly id = input<string>();
  readonly t = input<string>();

  protected readonly record = signal<AedRecord | null>(null);
  protected readonly loadError = signal('');
  protected readonly sendError = signal('');
  protected readonly done = signal<'potwierdzenie' | 'sygnal' | null>(null);

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
  protected readonly values = new FormGroup(
    Object.fromEntries(
      [...this.coordinates, ...this.place, ...this.spot, this.access, this.hours, this.hoursNote].map((field) => [
        field.name,
        aedControl(field, this.required.includes(field.name)),
      ]),
    ),
  );
  protected readonly stan = new FormControl<AedCondition | null>(null, Validators.required);
  protected readonly uwagi = new FormControl('');
  protected readonly form = new FormGroup({ values: this.values, stan: this.stan, uwagi: this.uwagi });

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
        this.values.patchValue(record);
      },
      error: (error) => this.loadError.set(aedErrorMessage(error)),
    });
  }

  /** One tap: read the phone position and put it into the form (manager) or attach it to the signal. */
  protected locate(): void {
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
    const filled = Object.entries(this.values.getRawValue()).filter(([, value]) => value !== null && value !== '');
    const body = {
      ...Object.fromEntries(filled),
      t: this.t(),
      stan: this.stan.value,
      uwagi: this.uwagi.value || undefined,
    };
    this.api.confirm(this.id(), body).subscribe({
      next: (record) => {
        this.record.set(record);
        this.finish('potwierdzenie');
      },
      error: (error) => this.sendError.set(aedErrorMessage(error)),
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
  private finish(done: 'potwierdzenie' | 'sygnal'): void {
    this.sendError.set('');
    this.done.set(done);
    afterNextRender(() => this.host.nativeElement.querySelector<HTMLElement>('#aed-done')?.focus(), {
      injector: this.injector,
    });
  }
}
