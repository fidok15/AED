import { aedMockCsv } from './aed-mock.service';
import { aedRequired } from './aed-schema';

describe('aedMockCsv', () => {
  const header = aedRequired('sprzedaz').join(',');
  const row =
    'Philips,HeartStart FRx,TEST-0001,2026-03-01,2028-03-31,2030-01-31,Urząd Miasta Legionowo,aed@um.legionowo.pl';

  it('accepts a file that fits profile sprzedaz and saves it only when asked', () => {
    expect(aedMockCsv(`\uFEFF${header}\r\n${row}\r\n`).podsumowanie).toMatchObject({
      wiersze: 1,
      przyjete: 1,
      bledy: 0,
    });
    expect(aedMockCsv(`${header}\n${row}`).przyjete).toEqual([]);

    const saved = aedMockCsv(`${header}\n${row}`, 'Firma testowa');
    expect(saved.przyjete[0].link_aktywacyjny).toContain(`/aed/qr/${saved.przyjete[0].id_aed}?t=`);
    expect(aedMockCsv(`${header}\n${row}`).podsumowanie.duplikaty).toBe(1);
  });

  it('reports a missing column, an empty required cell and a malformed date', () => {
    const report = aedMockCsv(`${header.replace(',model', '')}\nPhilips,,01.03.2026`);
    expect(report.podsumowanie.odrzucone).toBe(1);
    expect(report.problemy.map((problem) => `${problem.wiersz}:${problem.pole}`)).toEqual(
      expect.arrayContaining(['1:model', '2:numer_seryjny', '2:data_produkcji']),
    );
  });
});
