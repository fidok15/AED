import { aedHoursFromRows, aedHoursRows, aedIsHoliday, aedOpenNow, aedRowsFromHours } from './aed-hours';

describe('aedOpenNow', () => {
  const tuesdayMorning = new Date(2026, 10, 24, 10, 0); // 24 Nov 2026, Tuesday
  const saturday = new Date(2026, 10, 28, 10, 0);
  const independenceDay = new Date(2026, 10, 11, 10, 0); // Wednesday, public holiday

  it('reads the plain forms', () => {
    expect(aedOpenNow('24/7', saturday)).toBe('dostepny');
    expect(aedOpenNow('Mo-Fr 08:00-16:00', tuesdayMorning)).toBe('dostepny');
    expect(aedOpenNow('Mo-Fr 08:00-16:00', saturday)).toBe('zamkniety');
    expect(aedOpenNow('Mo 08:00-17:00; Tu-Fr 12:00-15:00; Sa-Su, PH off', tuesdayMorning)).toBe('zamkniety');
    expect(aedOpenNow('06:00-22:00', saturday)).toBe('dostepny');
  });

  it('closes on public holidays when the value says so', () => {
    expect(aedOpenNow('Mo-Fr 07:30-15:30; Sa-Su, PH off', independenceDay)).toBe('zamkniety');
    expect(aedOpenNow('Mo-Fr 07:30-15:30', independenceDay)).toBe('dostepny');
    expect(aedIsHoliday(new Date(2026, 3, 6))).toBe(true); // Easter Monday 2026
    expect(aedIsHoliday(new Date(2026, 5, 4))).toBe(true); // Corpus Christi 2026
    expect(aedIsHoliday(tuesdayMorning)).toBe(false);
  });

  it('never guesses', () => {
    expect(aedOpenNow('', tuesdayMorning)).toBe('nieznane');
    expect(aedOpenNow(null, tuesdayMorning)).toBe('nieznane');
    expect(aedOpenNow('sunrise-sunset', tuesdayMorning)).toBe('nieznane');
    expect(aedOpenNow('Mo-Fr 08:00-16:00; Dec 24 off', tuesdayMorning)).toBe('nieznane');
    expect(aedOpenNow('Mo-Su 22:00-06:00', tuesdayMorning)).toBe('nieznane');
    expect(aedOpenNow('W godzinach pracy urzędu', tuesdayMorning)).toBe('nieznane');
  });
});

describe('hours picker', () => {
  it('writes opening_hours syntax and reads its own output back', () => {
    const rows = aedHoursRows();
    expect(aedHoursFromRows(rows)).toBe('Mo-Fr 08:00-16:00');
    rows[1].open = true;
    expect(aedHoursFromRows(rows)).toBe('Mo-Fr 08:00-16:00; Sa 09:00-13:00');
    expect(aedHoursFromRows(aedRowsFromHours('Mo-Fr 07:30-15:30; Su 10:00-14:00'))).toBe(
      'Mo-Fr 07:30-15:30; Su 10:00-14:00',
    );
    expect(aedOpenNow(aedHoursFromRows(rows), new Date(2026, 10, 28, 10, 0))).toBe('dostepny'); // a Saturday
  });

  it('gives nothing for an empty or reversed range and does not touch other syntax', () => {
    const rows = aedHoursRows();
    rows[0].to = '07:00';
    expect(aedHoursFromRows(rows)).toBe('');
    expect(aedHoursFromRows(rows.map((row) => ({ ...row, open: false })))).toBe('');
    expect(aedRowsFromHours('Mo-Fr 07:30-15:30; Sa-Su, PH off')).toBeNull();
    expect(aedRowsFromHours('24/7')).toBeNull();
  });
});
