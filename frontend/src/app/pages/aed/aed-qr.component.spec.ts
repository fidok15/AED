import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { SeoService } from '@app/services/seo.service';
import { AedApiService, AedRecord } from './aed-api.service';
import { AedQrComponent } from './aed-qr.component';

describe('AedQrComponent, manager view', () => {
  const inDays = (days: number) => new Date(Date.now() + days * 86_400_000).toISOString().slice(0, 10);
  // A record the manager has already completed once; the service sends every value as text.
  const record = (changes: Partial<AedRecord> = {}): AedRecord => ({
    id_aed: 'AED-TEST00000001',
    status: 'aktywny',
    kompletnosc: '90',
    nazwa: 'Urząd Demonstracyjny',
    miejscowosc: 'Fikcyjnowo',
    szerokosc_geograficzna: '52.1',
    dlugosc_geograficzna: '21.0',
    nazwa_ulicy: 'Stara',
    opis_lokalizacji: 'Stary opis, już nieprawdziwy',
    dostep: 'publiczny',
    godziny_dostepu: '24/7',
    godziny_dostepu_opis: '',
    data_waznosci_baterii: inDays(400),
    data_waznosci_elektrod: inDays(400),
    data_weryfikacji: '2026-11-21',
    ...changes,
  });

  let confirm: jest.Mock;
  let fixture: ComponentFixture<AedQrComponent>;
  let page: HTMLElement;

  const open = (loaded: AedRecord, answer: AedRecord) => {
    confirm = jest.fn(() => of(answer));
    TestBed.configureTestingModule({
      imports: [AedQrComponent],
      providers: [
        { provide: AedApiService, useValue: { device: () => of(loaded), confirm } },
        { provide: SeoService, useValue: { setPageTitle: () => undefined } },
      ],
    });
    fixture = TestBed.createComponent(AedQrComponent);
    fixture.componentRef.setInput('id', loaded.id_aed);
    fixture.componentRef.setInput('t', 'token');
    fixture.detectChanges();
    page = fixture.nativeElement;
  };
  const type = (selector: string, value: string) => {
    const input = page.querySelector<HTMLInputElement | HTMLTextAreaElement>(selector);
    input.value = value;
    input.dispatchEvent(new Event('input'));
    fixture.detectChanges();
  };
  const choose = (selector: string) => {
    page.querySelector<HTMLInputElement>(selector).click();
    fixture.detectChanges();
  };
  const submit = () => {
    page.querySelector('form').dispatchEvent(new Event('submit'));
    fixture.detectChanges();
  };

  it('says the device is active only when the service made it active', () => {
    open(record(), record({ status: 'aktywny' }));
    choose('input[name="aed-stan"][value="sprawny"]');
    submit();

    expect(page.querySelector('#aed-done').textContent).toContain('Dane potwierdzone');
    expect(page.querySelector('.aed-result').textContent).toContain('status „aktywny”');
    expect(page.querySelector('.aed-result__mark--problem')).toBeNull();
  });

  it('reports a problem as a problem: no "aktywny", no success mark', () => {
    open(record(), record({ status: 'niepotwierdzony' }));
    choose('input[name="aed-stan"][value="problem"]');
    type('#aed-uwagi', 'Mija termin ważności baterii');
    submit();

    expect(confirm.mock.calls[0][1]).toMatchObject({ stan: 'problem', uwagi: 'Mija termin ważności baterii' });
    expect(page.querySelector('#aed-done').textContent).toContain('Zgłoszenie problemu zapisane');
    expect(page.querySelector('.aed-result').textContent).toContain('nie jest teraz pokazywane jako aktywne');
    expect(page.querySelector('.aed-result').textContent).toContain('Niepotwierdzony');
    expect(page.querySelector('.aed-result').textContent).not.toContain('status „aktywny”');
    expect(page.querySelector('.aed-result__mark--problem')).not.toBeNull();
  });

  it('sends an emptied optional field as an empty string and leaves untouched empty fields out', () => {
    open(record(), record());
    type('#aed-opis_lokalizacji', '');
    type('#aed-nazwa_ulicy', '');
    choose('input[name="aed-stan"][value="sprawny"]');
    submit();

    const body = confirm.mock.calls[0][1];
    expect(body.opis_lokalizacji).toBe('');
    expect(body.nazwa_ulicy).toBe('');
    expect(body.nazwa).toBe('Urząd Demonstracyjny');
    expect('godziny_dostepu_opis' in body).toBe(false); // was empty and nobody touched it
    expect('kod_pocztowy' in body).toBe(false);
  });

  it('lets the manager enter new battery and electrode dates, first on the page when a date is close', () => {
    const soon = inDays(20);
    open(record({ data_waznosci_baterii: soon }), record());
    const cards = Array.from(page.querySelectorAll('form .aed-card')).map(
      (card) => card.querySelector('h2').textContent,
    );
    expect(cards[0]).toContain('Bateria i elektrody');
    expect(page.querySelector('.aed-message--warn').textContent).toContain(soon);
    expect(page.querySelector<HTMLInputElement>('#aed-data_waznosci_baterii').type).toBe('date');

    const next = inDays(1500);
    type('#aed-data_waznosci_baterii', next);
    choose('input[name="aed-stan"][value="sprawny"]');
    submit();
    expect(confirm.mock.calls[0][1]).toMatchObject({ data_waznosci_baterii: next });
  });

  it('does not prefill a point known only from OpenStreetMap and sends the owner contact', () => {
    open(record({ licencja: 'ODbL 1.0', status: 'niepotwierdzony' }), record());
    expect(page.querySelector<HTMLInputElement>('#aed-nazwa').value).toBe('');
    expect(page.querySelector<HTMLInputElement>('#aed-opis_lokalizacji').value).toBe('');
    expect(page.textContent).toContain('OpenStreetMap');

    type('#aed-nazwa', 'Szkoła nr 1');
    type('#aed-miejscowosc', 'Fikcyjnowo');
    type('#aed-szerokosc_geograficzna', '52.2');
    type('#aed-dlugosc_geograficzna', '21.1');
    choose('input[name="aed-dostep"][value="publiczny"]');
    choose('input[name="aed-hours-mode"][value="all"]');
    type('#aed-dysponent_email', 'aed@urzad.example');
    choose('input[name="aed-stan"][value="sprawny"]');
    submit();
    const body = confirm.mock.calls[0][1];
    expect(body).toMatchObject({ nazwa: 'Szkoła nr 1', godziny_dostepu: '24/7', dysponent_email: 'aed@urzad.example' });
    expect('opis_lokalizacji' in body).toBe(false); // the OSM value was never put into the form
  });

  it('keeps the battery and electrode step last when no date is close', () => {
    open(record(), record());
    const cards = Array.from(page.querySelectorAll('form .aed-card')).map(
      (card) => card.querySelector('h2').textContent,
    );
    expect(cards[cards.length - 1]).toContain('Bateria i elektrody');
    expect(page.querySelector('.aed-message--warn')).toBeNull();
  });
});
