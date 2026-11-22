import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { LocalizeRouterService } from '@gilsdav/ngx-translate-router';
import { of } from 'rxjs';

import { SeoService } from '@app/services/seo.service';
import { AedApiService, AedSubmission } from './aed-api.service';
import { AedCompanyComponent } from './aed-company.component';

describe('AedCompanyComponent validation report', () => {
  it('keeps table semantics for the problem cards and labels every value', () => {
    const api = {
      account: signal({ id: 2, nazwa: 'Pulsar', rola: 'firma', typ_podmiotu: 'sprzedawca' }),
      sellers: () => of({ dane: [], progi: {} }),
      submissions: () => of([]),
      stats: () => of({}),
    };
    TestBed.configureTestingModule({
      imports: [AedCompanyComponent],
      providers: [
        provideRouter([]),
        { provide: AedApiService, useValue: api },
        { provide: SeoService, useValue: { setPageTitle: () => undefined } },
        {
          provide: LocalizeRouterService,
          useValue: { translateRoute: (path: string) => path, routerEvents: of(), parser: { currentLang: 'pl' } },
        },
      ],
    });
    const fixture = TestBed.createComponent(AedCompanyComponent);
    const report = {
      id: 1,
      utworzono: '2026-11-22T01:00:00',
      podsumowanie: { wiersze: 2, przyjete: 1, odrzucone: 1, bledy: 1, ostrzezenia: 0, duplikaty: 0 },
      problemy: [
        {
          wiersz: 3,
          pole: 'data_produkcji',
          poziom: 'blad',
          kod: 'format_daty',
          komunikat: 'Wpisz datę jako 2024-03-15.',
        },
      ],
      przyjete: [],
    } as unknown as AedSubmission;
    fixture.componentInstance['report'].set(report);
    fixture.detectChanges();

    const table: HTMLElement = fixture.nativeElement.querySelector('table.aed-problems');
    expect(table.getAttribute('role')).toBe('table');
    expect(Array.from(table.querySelectorAll('th')).map((th) => th.getAttribute('role'))).toEqual(
      Array(4).fill('columnheader'),
    );
    const row = table.querySelector('tbody tr');
    expect(row.getAttribute('role')).toBe('row');
    expect(row.classList).toContain('aed-problems__row--error');
    const cells = Array.from(row.querySelectorAll('td'));
    expect(cells.map((td) => td.getAttribute('role'))).toEqual(Array(4).fill('cell'));
    expect(cells[0].textContent).toContain('Wiersz 3');
    expect(cells[2].textContent.trim()).toBe('Błąd');
    expect(cells[3].textContent).toContain('Co poprawić: Wpisz datę');
    // Card labels repeat the column headers, so they are hidden from screen readers.
    row
      .querySelectorAll('.aed-problems__label')
      .forEach((label) => expect(label.getAttribute('aria-hidden')).toBe('true'));
  });
});
