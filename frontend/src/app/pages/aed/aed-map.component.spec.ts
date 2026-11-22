import { aedDevices, aedDistanceM, aedDistanceText } from './aed-map.component';

describe('aed map helpers', () => {
  it('counts devices with the Polish plural', () => {
    expect([1, 2, 4, 5, 12, 22, 25, 112].map(aedDevices)).toEqual([
      '1 urządzenie',
      '2 urządzenia',
      '4 urządzenia',
      '5 urządzeń',
      '12 urządzeń',
      '22 urządzenia',
      '25 urządzeń',
      '112 urządzeń',
    ]);
  });

  it('gives straight-line distance like the service (0.01° of latitude ≈ 1112 m)', () => {
    expect(Math.round(aedDistanceM({ lat: 52, lon: 21 }, 52.01, 21))).toBe(1112);
    expect(aedDistanceText(107.4)).toBe('107 m w linii prostej');
    expect(aedDistanceText(1112)).toBe('1,1 km w linii prostej');
  });
});
