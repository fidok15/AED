// "Is it accessible right now?" from `godziny_dostepu` (opening_hours syntax of OpenStreetMap).
// Only the plain forms are read: 24/7, and rules like "Mo-Fr 08:00-16:00; Sa 09:00-13:00; Su,PH off".
// Anything else (months, sunrise, comments, hours past midnight) gives `nieznane` – never a guess.

export type AedOpenState = 'dostepny' | 'zamkniety' | 'nieznane';

export const AED_OPEN_LABELS: Record<AedOpenState, string> = {
  dostepny: 'Dostępny teraz',
  zamkniety: 'Teraz zamknięty',
  nieznane: 'Dostępność teraz nieznana',
};

const DAYS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];
const DAY = '(?:Mo|Tu|We|Th|Fr|Sa|Su|PH)';
const SPAN = '\\d{1,2}:\\d{2}-\\d{1,2}:\\d{2}';
const RULE = new RegExp(`^(?:(${DAY}(?:\\s*[-,]\\s*${DAY})*)\\s+)?(off|closed|${SPAN}(?:\\s*,\\s*${SPAN})*)$`);

/** Wall-clock time in Poland, whatever the time zone of the viewer. */
export const aedWarsawNow = (): Date =>
  new Date(new Date().toLocaleString('sv-SE', { timeZone: 'Europe/Warsaw' }).replace(' ', 'T'));

/** Easter Sunday (anonymous Gregorian algorithm). */
function easter(year: number): Date {
  const a = year % 19;
  const b = Math.floor(year / 100);
  const c = year % 100;
  const h = (19 * a + b - Math.floor(b / 4) - Math.floor((b - Math.floor((b + 8) / 25) + 1) / 3) + 15) % 30;
  const l = (32 + 2 * (b % 4) + 2 * Math.floor(c / 4) - h - (c % 4)) % 7;
  const m = Math.floor((a + 11 * h + 22 * l) / 451);
  return new Date(year, Math.floor((h + l - 7 * m + 114) / 31) - 1, ((h + l - 7 * m + 114) % 31) + 1);
}

/** Public holidays in Poland (24 December since 2025). */
export function aedIsHoliday(date: Date): boolean {
  const fixed = ['1-1', '1-6', '5-1', '5-3', '8-15', '11-1', '11-11', '12-25', '12-26'];
  if (date.getFullYear() >= 2025) fixed.push('12-24');
  if (fixed.includes(`${date.getMonth() + 1}-${date.getDate()}`)) return true;
  const midnight = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const sinceEaster = Math.round((midnight.getTime() - easter(date.getFullYear()).getTime()) / 86_400_000);
  return [0, 1, 49, 60].includes(sinceEaster); // Easter, Easter Monday, Pentecost, Corpus Christi
}

function dayMatches(days: string, today: string, holiday: boolean): boolean {
  return days.split(',').some((part) => {
    const [from, to = from] = part.split('-').map((day) => day.trim());
    if (from === 'PH' || to === 'PH') return holiday && from === to;
    const start = DAYS.indexOf(from);
    const length = (DAYS.indexOf(to) - start + 7) % 7;
    return (DAYS.indexOf(today) - start + 7) % 7 <= length;
  });
}

export function aedOpenNow(hours: string | null | undefined, now = aedWarsawNow()): AedOpenState {
  const value = (hours ?? '').trim();
  if (!value) return 'nieznane';
  if (value === '24/7') return 'dostepny';

  const rules = value
    .split(';')
    .map((rule) => rule.trim())
    .filter(Boolean)
    .map((rule) => RULE.exec(rule));
  if (rules.some((match) => !match)) return 'nieznane';

  const holiday = aedIsHoliday(now);
  const holidayRules = holiday && rules.some(([, days]) => days?.includes('PH'));
  const today = DAYS[now.getDay()];
  const minute = now.getHours() * 60 + now.getMinutes();
  let open = false; // hours are given, so a day without a rule is a closed day

  for (const [, days, times] of rules) {
    // on a public holiday the PH rules decide, when the value has any
    if (holidayRules ? !days?.includes('PH') : days && !dayMatches(days, today, holiday)) continue;
    if (times === 'off' || times === 'closed') {
      open = false;
      continue;
    }
    const spans = times.split(',').map((span) =>
      span
        .trim()
        .split('-')
        .map((time) => +time.split(':')[0] * 60 + +time.split(':')[1]),
    );
    if (spans.some(([from, to]) => to <= from)) return 'nieznane'; // past midnight: not read
    open = spans.some(([from, to]) => minute >= from && minute < to);
  }
  return open ? 'dostepny' : 'zamkniety';
}
