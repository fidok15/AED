import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SeoService } from '@app/services/seo.service';
import { AedConverterAnalysis, AedConverterComponent } from './aed-converter.component';

describe('AedConverterComponent', () => {
  let fixture: ComponentFixture<AedConverterComponent>;
  let http: HttpTestingController;
  let page: HTMLElement;

  const analysis: AedConverterAnalysis = {
    plik: 'krosno.csv',
    format: 'csv',
    format_opis: 'Rozpoznano po treści pliku: CSV.',
    kodowanie: 'UTF-8',
    separator: 'przecinek',
    wiersze: 2,
    kolumny: [
      { kolumna: 'Nazwa', przyklady: ['Defibrylator'], pole: '', powod: '' },
      { kolumna: 'Lokalizacja', przyklady: ['Basen'], pole: 'nazwa', powod: 'nazwa kolumny jak w pliku: Krosno' },
      { kolumna: 'Adres', przyklady: ['ul. Jasna 1, 38-400 Krosno'], pole: '_adres', powod: 'wartości' },
    ],
    pola: [
      { pole: '_adres', tytul: 'Adres w jednym polu' },
      { pole: 'nazwa', tytul: 'Nazwa miejsca' },
    ],
    pola_stale: [{ pole: 'dostep', tytul: 'Dostęp', wartosci: ['publiczny', 'ograniczony', 'prywatny'] }],
    uwagi: [],
    ostrzezenia: [],
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [AedConverterComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: SeoService, useValue: { setPageTitle: () => undefined } },
      ],
    });
    fixture = TestBed.createComponent(AedConverterComponent);
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    page = fixture.nativeElement;
  });

  const upload = () => {
    const input = page.querySelector<HTMLInputElement>('#aed-conv-plik');
    Object.defineProperty(input, 'files', { value: [new File(['a,b\n1,2\n'], 'krosno.csv')] });
    input.dispatchEvent(new Event('change'));
    http.expectOne('/api/aed/konwerter/analiza').flush(analysis);
    fixture.detectChanges();
  };

  it('prefills the proposal, sends the mapping and offers the converted file', () => {
    upload();
    const selects = page.querySelectorAll<HTMLSelectElement>('select[id^="aed-conv-col-"]');
    expect(Array.from(selects).map((select) => select.value)).toEqual(['', 'nazwa', '_adres']);
    expect(page.querySelector('label[for="aed-conv-col-1"]').textContent).toContain('Lokalizacja');

    const access = page.querySelector<HTMLSelectElement>('#aed-conv-const-dostep');
    access.value = 'publiczny';
    access.dispatchEvent(new Event('change'));
    page.querySelector<HTMLButtonElement>('button.btn-primary').click();
    const request = http.expectOne('/api/aed/konwerter/konwersja');
    const body = request.request.body as FormData;
    expect(JSON.parse(body.get('mapowanie') as string)).toEqual({ Nazwa: '', Lokalizacja: 'nazwa', Adres: '_adres' });
    expect(JSON.parse(body.get('stale') as string)).toEqual({ dostep: 'publiczny' });
    expect(body.get('geokodowanie')).toBeNull();
    expect(page.querySelector('#aed-conv-geo-note')).toBeNull(); // the server did not offer geocoding
    request.flush({
      nazwa_pliku: 'krosno-wykaz-aed.csv',
      plik_csv: 'nazwa\nBasen\n',
      raport: {
        status: 'przyjety',
        wiersze: 2,
        poprawne: 2,
        odrzucone: 0,
        poza_wykazem_krajowym: 0,
        kompletnosc_srednia: 40.1,
        problemy: [],
        problemy_razem: 0,
        poprawki: [],
        normalizacje: [
          {
            kolumna: 'Dostęp',
            pole: 'dostep',
            liczba: 1,
            z: 'Publiczny',
            na: 'publiczny',
            komunikat: 'Kolumna „Dostęp” (Dostęp): ujednolicono zapis 1 z 2 wartości, np. „Publiczny” → „publiczny”.',
          },
        ],
        ukryte_pola: ['dysponent_email'],
        ukryte_komunikat:
          'Kolumny E-mail dysponenta są w pobranym pliku puste: kontakt i numer seryjny nie trafiają do pliku publicznego.',
        bez_wspolrzednych: 1,
        bez_wspolrzednych_komunikat: '1 wierszy ma adres bez współrzędnych – nie trafią do wykazu.',
      },
    });
    fixture.detectChanges();
    expect(page.textContent).toContain('1 wiersz ma adres bez współrzędnych – nie trafi do wykazu');
    const link = page.querySelector<HTMLAnchorElement>('a[download]');
    expect(link.textContent).toContain('Pobierz wykaz w standardzie (CSV)');
    expect(link.getAttribute('download')).toBe('krosno-wykaz-aed.csv');
    expect(page.textContent).toContain('Wykaz AED: TAK');
    expect(page.textContent).toContain('„Publiczny” → „publiczny”');
    expect(page.textContent).toContain('nie trafiają do pliku publicznego');
  });

  it('sends addresses to GUGiK only when the user ticks the box, and lists the filled rows', () => {
    const input = page.querySelector<HTMLInputElement>('#aed-conv-plik');
    Object.defineProperty(input, 'files', { value: [new File(['a\n1\n'], 'krakow.docx')] });
    input.dispatchEvent(new Event('change'));
    http.expectOne('/api/aed/konwerter/analiza').flush({ ...analysis, geokodowanie_dostepne: true });
    fixture.detectChanges();
    const box = page.querySelector<HTMLInputElement>('input[aria-describedby="aed-conv-geo-note"]');
    expect(box.checked).toBe(false);
    expect(page.querySelector('#aed-conv-geo-note').textContent).toContain('GUGiK');
    box.click();
    page.querySelector<HTMLButtonElement>('button.btn-primary').click();
    const request = http.expectOne('/api/aed/konwerter/konwersja');
    expect((request.request.body as FormData).get('geokodowanie')).toBe('1');
    request.flush({
      nazwa_pliku: 'krakow-wykaz-aed.csv',
      plik_csv: 'nazwa\n',
      raport: {
        status: 'czesciowo',
        wiersze: 2,
        poprawne: 1,
        odrzucone: 1,
        poza_wykazem_krajowym: 0,
        kompletnosc_srednia: 30,
        problemy: [],
        problemy_razem: 0,
        poprawki: [],
        normalizacje: [],
        ukryte_pola: [],
        ukryte_komunikat: '',
        bez_wspolrzednych: 1,
        bez_wspolrzednych_komunikat: '',
        geokodowanie: {
          komunikat: 'Adresy z pliku wysłano do usługi GUGiK.',
          uzupelnione: 1,
          nieuzupelnione: 1,
          wiersze_uzupelnione: [
            { wiersz: 1, nazwa: 'Dworzec', adres: 'Kraków, Bosacka 18', szerokosc: 50.07, dlugosc: 19.95, uwaga: '' },
          ],
          wiersze_nieuzupelnione: [{ wiersz: 2, nazwa: 'Urząd', powod: 'usługa nie znalazła punktu adresowego' }],
        },
      },
    });
    fixture.detectChanges();
    expect(page.textContent).toContain('wysłano do usługi GUGiK');
    expect(page.textContent).toContain('punkt adresowy Kraków, Bosacka 18');
    expect(page.textContent).toContain('Wiersz 2 (Urząd): usługa nie znalazła punktu adresowego');
  });

  it('drops the answer for a file replaced before the analysis came back', () => {
    const input = page.querySelector<HTMLInputElement>('#aed-conv-plik');
    let files = [new File(['a\n1\n'], 'a.csv')];
    Object.defineProperty(input, 'files', { get: () => files });
    input.dispatchEvent(new Event('change'));
    const first = http.expectOne('/api/aed/konwerter/analiza');
    files = [new File(['b\n2\n'], 'b.csv')];
    input.dispatchEvent(new Event('change'));
    const second = http.expectOne('/api/aed/konwerter/analiza');
    expect(first.cancelled).toBe(true);
    expect((second.request.body as FormData).get('plik')).toEqual(files[0]);
    second.flush({ ...analysis, plik: 'b.csv' });
    fixture.detectChanges();
    expect(page.textContent).toContain('b.csv');
  });

  it('does not send a mapping with one field for two columns', () => {
    upload();
    const first = page.querySelector<HTMLSelectElement>('#aed-conv-col-0');
    first.value = 'nazwa';
    first.dispatchEvent(new Event('change'));
    fixture.detectChanges();
    page.querySelector<HTMLButtonElement>('button.btn-primary').click();
    fixture.detectChanges();
    http.expectNone('/api/aed/konwerter/konwersja');
    expect(page.querySelector('[role="alert"]').textContent).toContain('Nazwa miejsca');
  });
});
