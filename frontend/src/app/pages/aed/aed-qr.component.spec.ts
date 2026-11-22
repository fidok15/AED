import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { SeoService } from '@app/services/seo.service';
import { AedApiService, AedRecord } from './aed-api.service';
import { AedQrComponent } from './aed-qr.component';

describe('AedQrComponent, manager view', () => {
  const inDays = (days: number) => new Date(Date.now() + days * 86_400_000).toISOString().slice(0, 10);
  // A record the manager has already completed once; the service sends every value as text.
  // `waznosc_do` is the last valid day computed by the service (aed_standard.valid_until).
  const record = (changes: Partial<AedRecord> = {}): AedRecord => {
    const base = { ...fields(), ...changes };
    const waznosc_do = {
      data_waznosci_baterii: String(base['data_waznosci_baterii']),
      data_waznosci_elektrod: String(base['data_waznosci_elektrod']),
    };
    return { ...base, waznosc_do } as unknown as AedRecord;
  };
  const fields = (): AedRecord => ({
    id_aed: 'AED-TEST00000001',
    status: 'zweryfikowany',
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

  it('says the device is verified and ready when the service confirmed it', () => {
    open(record(), record({ status: 'zweryfikowany', stan_urzadzenia: 'gotowy', data_stanu: '2026-11-22' }));
    choose('input[name="aed-stan"][value="sprawny"]');
    submit();

    expect(page.querySelector('#aed-done').textContent).toContain('Dane potwierdzone');
    expect(page.querySelector('.aed-result').textContent).toContain('status „Zweryfikowany”');
    expect(page.querySelector('.aed-result__mark--problem')).toBeNull();
    expect(page.querySelector('.aed-device').textContent).toContain('gotowe do użycia (potwierdzone 22.11.2026)');
  });

  it('reports a problem by the device condition: data stay verified, the device is temporarily unavailable', () => {
    open(
      record(),
      record({ status: 'zweryfikowany', stan_urzadzenia: 'czasowo_niedostepny', data_stanu: '2026-11-22' }),
    );
    choose('input[name="aed-stan"][value="problem"]');
    type('#aed-uwagi', 'Mija termin ważności baterii');
    submit();

    expect(confirm.mock.calls[0][1]).toMatchObject({ stan: 'problem', uwagi: 'Mija termin ważności baterii' });
    expect(page.querySelector('#aed-done').textContent).toContain('Zgłoszenie problemu zapisane');
    const result = page.querySelector('.aed-result').textContent;
    expect(result).toContain('czasowo niedostępne');
    expect(result).toContain('Dostępne teraz');
    expect(result).toContain('Jest na miejscu i jest gotowe do użycia');
    expect(result).not.toContain('Dane potwierdzone');
    expect(page.querySelector('.aed-device').textContent).toContain('czasowo niedostępne (od 22.11.2026)');
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

  it('lets the manager enter new battery and electrode dates after the required steps, flagging a close date on top', () => {
    const soon = inDays(20);
    open(record({ data_waznosci_baterii: soon }), record());
    const cards = Array.from(page.querySelectorAll('form .aed-card')).map(
      (card) => card.querySelector('h2').textContent,
    );
    expect(cards[0]).toContain('Gdzie znajduje się urządzenie');
    expect(cards[cards.length - 1]).toContain('Bateria i elektrody');
    expect(page.querySelector('.aed-device__expiry').textContent).toMatch(
      /Bateria: ważna do .* r\. \(zostało 20 dni\)/,
    );
    // RRRR-MM-DD or RRRR-MM: one text box, checked against the schema pattern.
    expect(page.querySelector<HTMLInputElement>('#aed-data_waznosci_baterii').type).toBe('text');
    type('#aed-data_waznosci_baterii', '2028-13');
    page.querySelector('#aed-data_waznosci_baterii').dispatchEvent(new Event('blur'));
    fixture.detectChanges();
    expect(page.querySelector('#aed-data_waznosci_baterii-error').textContent).toContain('RRRR-MM');

    const next = '2030-03';
    type('#aed-data_waznosci_baterii', next);
    choose('input[name="aed-stan"][value="sprawny"]');
    submit();
    expect(confirm.mock.calls[0][1]).toMatchObject({ data_waznosci_baterii: next });
  });

  it('flags a month-only expiry date from the last day of that month (waznosc_do of the service)', () => {
    const loaded = record();
    (loaded as unknown as { waznosc_do: Record<string, string> }).waznosc_do.data_waznosci_elektrod = inDays(10);
    open({ ...loaded, data_waznosci_elektrod: '2026-11' }, record());
    expect(page.querySelector('.aed-device__expiry').textContent).toMatch(/Elektrody: ważne do .* \(zostało 10 dni\)/);
  });

  it('sends the floor inside a building and the phone position with its method', () => {
    open(record({ wewnatrz_budynku: 'nie' }), record());
    expect(page.querySelector('#aed-pietro')).toBeNull();
    choose('input[name="aed-wewnatrz_budynku"][value="tak"]');
    type('#aed-pietro', '-1');

    const geolocation = {
      getCurrentPosition: (ok: PositionCallback) =>
        ok({ coords: { latitude: 52.2297, longitude: 21.0122, accuracy: 8 } } as GeolocationPosition),
    };
    Object.defineProperty(navigator, 'geolocation', { value: geolocation, configurable: true });
    page.querySelector<HTMLButtonElement>('.aed-card .aed-button--secondary').click();
    choose('input[name="aed-stan"][value="sprawny"]');
    submit();
    expect(confirm.mock.calls[0][1]).toMatchObject({
      pietro: '-1',
      szerokosc_geograficzna: 52.2297,
      sposob_ustalenia_polozenia: 'pomiar_przy_urzadzeniu',
    });
  });

  it('claims no position method for coordinates typed by hand and no floor outside a building', () => {
    open(record({ wewnatrz_budynku: 'nie', pietro: '2' }), record());
    type('#aed-szerokosc_geograficzna', '52.3');
    choose('input[name="aed-stan"][value="sprawny"]');
    submit();
    const body = confirm.mock.calls[0][1];
    expect(body.szerokosc_geograficzna).toBe('52.3'); // text box: the service reads the number
    expect('sposob_ustalenia_polozenia' in body).toBe(false);
    expect('pietro' in body).toBe(false);
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

  it('does not ask for the owner contact when the record has one', () => {
    open(record({ dysponent_email: 'aed@urzad.example' }), record());
    expect(page.querySelector('#aed-step-owner')).toBeNull();
  });

  it('asks for the owner contact when the record has none', () => {
    open(record(), record());
    expect(page.querySelector('#aed-step-owner')).not.toBeNull();
    type('#aed-dysponent_email', 'aed@gmina.example');
    choose('input[name="aed-stan"][value="sprawny"]');
    submit();
    expect(confirm.mock.calls[0][1]).toMatchObject({
      dysponent_email: 'aed@gmina.example',
      nazwa: 'Urząd Demonstracyjny',
    });
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
