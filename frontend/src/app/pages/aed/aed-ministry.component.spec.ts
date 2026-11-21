import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { LocalizeRouterService } from '@gilsdav/ngx-translate-router';
import { of } from 'rxjs';

import { SeoService } from '@app/services/seo.service';
import { AedApiService, AedMessage } from './aed-api.service';
import { AedMinistryComponent } from './aed-ministry.component';

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
    const api = {
      account: signal({ id: 1, nazwa: 'Ministerstwo', rola: 'ministerstwo', typ_podmiotu: 'ministerstwo' }),
      exportUrl: '/api/aed/eksport/dane-gov-pl.csv',
      stats: () =>
        of({ razem: 2, srednia_kompletnosc: 50, wg_statusu: {}, wg_zrodla: {}, dostawcy: 1, potwierdzone_90_dni: 0 }),
      duplicates: () => of({ dane: [], razem: 0 }),
      jobs: () => of([]),
      messages: () => of({ dane: [signalMessage, activation], razem: 2 }),
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
    const fixture = TestBed.createComponent(AedMinistryComponent);

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
