import cases from './aed-hours.cases.json';
import { aedHoursFromRows, aedHoursRows, aedIsHoliday, aedOpenNow, AedOpenState, aedRowsFromHours } from './aed-hours';

// The table is shared with aed_standard/hours.py (tests/test_hours.py), so both implementations answer alike.
describe('aedOpenNow', () => {
  it.each(cases.open_now as [string | null, string, AedOpenState][])('%p at %s is %s', (hours, at, expected) => {
    expect(aedOpenNow(hours, new Date(at))).toBe(expected);
  });

  it.each(cases.holiday as [string, boolean][])('public holiday %s: %p', (day, expected) => {
    expect(aedIsHoliday(new Date(`${day}T12:00`))).toBe(expected);
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
