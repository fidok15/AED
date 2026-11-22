import en from '../../../assets/i18n/en.json';
import pl from '../../../assets/i18n/pl.json';

describe('national AED list menu label', () => {
  it.each([
    ['pl', pl, 'Wykaz AED'],
    ['en', en, 'AED register'],
  ])('is translated in %s', (_lang, translations, label) => {
    expect(translations.Menu.AedList).toBe(label);
    expect(translations.Menu.AedList).not.toContain('—');
  });
});
