import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { LocalizeRouterService } from '@gilsdav/ngx-translate-router';
import { of } from 'rxjs';

import { SeoService } from '@app/services/seo.service';
import { AedApiService, AedDuplicate, AedMessage } from './aed-api.service';
import { AedMinistryComponent } from './aed-ministry.component';

function create({ messages = [] as AedMessage[], duplicates = [] as AedDuplicate[] }) {
  const api = {
    account: signal({ id: 1, nazwa: 'Ministerstwo', rola: 'ministerstwo', typ_podmiotu: 'ministerstwo' }),
    exportUrl: '/api/aed/eksport/dane-gov-pl.csv',
    stats: () =>
      of({ razem: 2, srednia_kompletnosc: 50, wg_statusu: {}, wg_zrodla: {}, dostawcy: 1, potwierdzone_90_dni: 0 }),
    duplicates: () => of({ dane: duplicates, razem: duplicates.length }),
    jobs: () => of([]),
    messages: () => of({ dane: messages, razem: messages.length }),
  };
  TestBed.configureTestingModule({
    imports: [AedMinistryComponent],
    providers: [
      provideRouter([]),
      { provide: AedApiService, useValue: api },
      { provide: SeoService, useValue: { setPageTitle: () => undefined } },
      { provide: LocalizeRouterService, useValue: { translateRoute: (path: string) => path.replace(/!/g, '') } },
    ],
  });
  return TestBed.createComponent(AedMinistryComponent);
}

describe('AedMinistryComponent duplicate review', () => {
  // Same serial number, the new submission has no position yet: odleglosc_m is null.
  const pair: AedDuplicate = {
    id: 7,
    rekord_a: {
      id_aed: 'AED-A',
      status: 'zweryfikowany',
      kompletnosc: 80,
      nazwa: 'Hala',
      miejscowosc: 'Marki',
      model: 'X1',
    },
    rekord_b: { id_aed: 'AED-B', status: 'zgloszony', kompletnosc: 40, nazwa: 'Hala', miejscowosc: '', model: 'X1' },
    odleglosc_m: null,
    podobienstwo: 0,
  };
  const rowTitles = (root: HTMLElement) =>
    Array.from(root.querySelectorAll('.aed-compare tbody th')).map((th) => th.textContent.trim());

  it('shows only differing fields until "Pokaż wszystkie pola" is pressed, never fields empty on both sides', () => {
    const fixture = create({ duplicates: [pair] });
    fixture.detectChanges(); // runs the effect that loads the pairs
    fixture.detectChanges();
    const root: HTMLElement = fixture.nativeElement;
    expect(root.textContent).toContain('odległość nieznana');

    const differing = rowTitles(root);
    expect(differing).toContain('Miejscowość');
    expect(differing).not.toContain('Nazwa miejsca');
    expect(root.querySelectorAll('.aed-compare__differs')).toHaveLength(differing.length);

    const toggle = Array.from(root.querySelectorAll('button')).find((b) =>
      b.textContent.includes('Pokaż wszystkie pola'),
    );
    expect(toggle.getAttribute('aria-pressed')).toBe('false');
    toggle.click();
    fixture.detectChanges();
    expect(toggle.getAttribute('aria-pressed')).toBe('true');
    const all = rowTitles(root);
    expect(all.length).toBeGreaterThan(differing.length);
    expect(all).toContain('Model');
    expect(all).not.toContain('Numer seryjny'); // empty in both records

    // The decision bar follows the comparison and holds the three choices.
    const bar = root.querySelector('.aed-decision');
    expect(bar.getAttribute('role')).toBe('group');
    expect(bar.querySelectorAll('button')).toHaveLength(3);
    expect(
      root.querySelector('.aed-scroll').compareDocumentPosition(bar) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });
});

describe('AedMinistryComponent outbox', () => {
  // Shapes as the service returns them: a bystander's signal has no manager link.
  const signalMessage: AedMessage = {
    id: 2,
    rodzaj: 'sygnal',
    id_aed: 'AED-SYGNAL000001',
    odbiorca: 'dysponent@demo.example',
    temat: 'Zgłoszenie dotyczące urządzenia AED AED-SYGNAL000001',
    tresc: 'Osoba postronna zgłosiła: uszkodzony. Rozbita szybka. Sprawdź urządzenie i potwierdź dane.',
    link: null,
    data: '2026-11-21T19:30:00',
  };
  const activation: AedMessage = {
    id: 1,
    rodzaj: 'aktywacja',
    id_aed: 'AED-AKTYWACJA001',
    odbiorca: 'dysponent@demo.example',
    temat: 'Aktywuj urządzenie AED AED-AKTYWACJA001',
    tresc: 'Uzupełnij lokalizację i godziny dostępu.',
    link: '/aed/qr/AED-AKTYWACJA001?t=token',
    data: '2026-11-21T19:00:00',
  };

  it('shows a message without a link instead of failing on it', () => {
    const fixture = create({ messages: [signalMessage, activation] });

    expect(() => fixture.detectChanges()).not.toThrow();
    fixture.detectChanges();

    const items: HTMLElement[] = Array.from(fixture.nativeElement.querySelectorAll('.aed-outbox__item'));
    expect(items).toHaveLength(2);
    expect(items[0].textContent).toContain('Zgłoszenie osoby postronnej');
    expect(items[0].textContent).toContain('Rozbita szybka');
    expect(items[0].textContent).toContain('AED-SYGNAL000001');
    expect(items[0].querySelector('a')).toBeNull();
    expect(items[1].querySelector('a').getAttribute('href')).toBe('/aed/qr/AED-AKTYWACJA001?t=token');
  });
});
