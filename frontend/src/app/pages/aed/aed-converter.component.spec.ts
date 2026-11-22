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
      },
    });
    fixture.detectChanges();
    const link = page.querySelector<HTMLAnchorElement>('a[download]');
    expect(link.textContent).toContain('Pobierz wykaz w standardzie (CSV)');
    expect(link.getAttribute('download')).toBe('krosno-wykaz-aed.csv');
    expect(page.textContent).toContain('Wykaz AED: TAK');
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
