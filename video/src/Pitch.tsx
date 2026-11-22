import React from 'react';
import {
  AbsoluteFill,
  Easing,
  Img,
  Series,
  interpolate,
  random,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {loadFont as loadLexend} from '@remotion/google-fonts/Lexend';
import {loadFont as loadAtkinson} from '@remotion/google-fonts/AtkinsonHyperlegible';
// Numbers on screen come only from our own report or a primary source (CLAUDE.md, hard rule 10).
import raport from '../../datasets/out/raport.json';
// The logo is never redrawn here: the wordmark comes from the official files.
import lockupKolor from '../../kampania/logo/svg/opiekun-aed-lockup-kolor.svg';
import lockupNegatyw from '../../kampania/logo/svg/opiekun-aed-lockup-negatyw.svg';

const HEAD = loadLexend('normal', {weights: ['600', '700'], subsets: ['latin', 'latin-ext']}).fontFamily;
const BODY = loadAtkinson('normal', {weights: ['400', '700'], subsets: ['latin', 'latin-ext']}).fontFamily;

// Brand palette – same values as kampania/ksiega-znaku and prezentacja-html.
const C = {
  navy: '#14274E',
  navy2: '#0E1C3A',
  blue: '#2456E6',
  sky: '#5F8DF5',
  amber: '#F28C28',
  grey: '#8A94A6',
  cream: '#F4F1EA',
  cream2: '#E9E3D6',
  muted: '#4E5A6E',
  white: '#FFFFFF',
};
// Cell colours of the mark: record states on a light and on a navy background (brand book).
const STATE = {
  light: {A: C.navy, Z: C.blue, U: C.sky, N: C.amber, W: C.grey},
  dark: {A: C.white, Z: '#6E97FF', U: '#3E5C99', N: C.amber, W: '#8FA0C2'},
};
const GRID = ['UA.AZ', 'AAAAN', '.AAW.', '..A..'];

// The Circuit (UK), state on 31.12.2023. Source: O'Sullivan et al., Resuscitation Plus 2024,
// https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004/ (opened and read on 22.11.2026).
const UK = {aed: 82108, guardians: 55235, unknownPct: 54, services: 14};

const zrodla = raport.rekordy_na_zrodlo as Record<string, {przed: number; po: number}>;
const miejskie = Object.entries(zrodla).filter(([k]) => k.startsWith('dane.gov.pl'));
const N = {
  rejestr: raport.rejestr_rekordy,
  zrodla: Object.keys(zrodla).length,
  miasta: miejskie.length,
  miastaRekordy: miejskie.reduce((s, [, v]) => s + v.przed, 0),
  warszawa: zrodla['um.warszawa.pl'].przed,
  osm: zrodla.openstreetmap.przed,
  polaczenia: raport.polaczenia.razem,
  eksport: raport.eksport_dane_gov_pl.rekordy,
  // "aktywny" is the name of this status in reports made before schema 0.3.0
  potwierdzone: ((s: Record<string, number>) => s.zweryfikowany ?? s.aktywny ?? 0)(raport.statusy),
};

const fmt = (n: number) =>
  Math.round(n)
    .toString()
    .replace(/\B(?=(\d{3})+(?!\d))/g, ' ');

const SCENES = {
  hook: 150,
  problem: 225,
  uk: 330,
  insight: 195,
  brand: 210,
  step1: 180,
  step2: 195,
  step3: 195,
  together: 240,
  benefits: 255,
  numbers: 180,
  cta: 210,
};
export const TOTAL = Object.values(SCENES).reduce((a, b) => a + b, 0);

// ---------- helpers ----------

const Dark = React.createContext(false);

const useIn = (delay = 0, damping = 200) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: frame - delay, fps, config: {damping}});
};

const Rise: React.FC<{delay?: number; y?: number; x?: number; style?: React.CSSProperties; children: React.ReactNode}> = ({
  delay = 0,
  y = 40,
  x = 0,
  style,
  children,
}) => {
  const p = useIn(delay);
  return <div style={{opacity: p, transform: `translate(${(1 - p) * x}px, ${(1 - p) * y}px)`, ...style}}>{children}</div>;
};

const Pop: React.FC<{delay?: number; style?: React.CSSProperties; children: React.ReactNode}> = ({delay = 0, style, children}) => {
  const p = useIn(delay, 12);
  return <div style={{transform: `scale(${p})`, opacity: Math.min(1, p * 2), ...style}}>{children}</div>;
};

const Scene: React.FC<{bg?: 'cream' | 'white' | 'navy'; children: React.ReactNode}> = ({bg = 'cream', children}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const o = interpolate(frame, [0, 12, durationInFrames - 12, durationInFrames], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const dark = bg === 'navy';
  return (
    <Dark.Provider value={dark}>
      <AbsoluteFill
        style={{
          opacity: o,
          color: dark ? C.white : C.navy,
          background: dark ? `radial-gradient(1400px 900px at 50% 30%, ${C.navy} 0%, ${C.navy2} 100%)` : C[bg],
        }}
      >
        {bg === 'cream' && (
          <AbsoluteFill style={{background: C.cream2, clipPath: 'polygon(62% 0, 100% 0, 100% 100%, 48% 100%)', opacity: 0.7}} />
        )}
        {children}
      </AbsoluteFill>
    </Dark.Provider>
  );
};

const useMuted = () => (React.useContext(Dark) ? 'rgba(255,255,255,.76)' : C.muted);

const Kicker: React.FC<{children: React.ReactNode}> = ({children}) => {
  const dark = React.useContext(Dark);
  return (
    <div style={{display: 'flex', alignItems: 'center', gap: 16, fontFamily: HEAD, fontSize: 28, fontWeight: 600, letterSpacing: 4, textTransform: 'uppercase', color: dark ? C.amber : C.blue}}>
      <div style={{width: 22, height: 22, borderRadius: 6, background: C.amber}} />
      {children}
    </div>
  );
};

const H: React.FC<{children: React.ReactNode; size?: number; style?: React.CSSProperties}> = ({children, size = 84, style}) => (
  <div style={{fontFamily: HEAD, fontSize: size, fontWeight: 700, lineHeight: 1.1, letterSpacing: '-0.03em', ...style}}>{children}</div>
);

const Em: React.FC<{children: React.ReactNode}> = ({children}) => {
  const dark = React.useContext(Dark);
  return <span style={{color: dark ? C.amber : C.blue}}>{children}</span>;
};

const Bullet: React.FC<{delay: number; children: React.ReactNode}> = ({delay, children}) => {
  const muted = useMuted();
  return (
    <Rise delay={delay} y={0} x={-40} style={{display: 'flex', gap: 22, alignItems: 'flex-start'}}>
      <div style={{marginTop: 14, width: 22, height: 22, borderRadius: 6, background: C.blue, flexShrink: 0}} />
      <div style={{fontSize: 38, lineHeight: 1.3, color: muted}}>{children}</div>
    </Rise>
  );
};

/** Cells of the mark as SVG rects; `k` scales sygnet units (cell 20, gap 4). */
const MarkCells: React.FC<{k?: number; delay?: number; step?: number; dark?: boolean}> = ({k = 1, delay = -999, step = 3, dark = false}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const colors = STATE[dark ? 'dark' : 'light'];
  let i = 0;
  return (
    <>
      {GRID.flatMap((row, r) =>
        [...row].map((s, c) => {
          if (s === '.') return null;
          const p = spring({frame: f - delay - i++ * step, fps, config: {damping: 11}});
          const x = (2 + c * 24) * k;
          const y = (14 + r * 24) * k;
          const style: React.CSSProperties = {transformBox: 'fill-box', transformOrigin: 'center', transform: `scale(${p})`};
          return s === 'W' ? (
            <rect key={`${r}${c}`} x={x + 1.4 * k} y={y + 1.4 * k} width={17.2 * k} height={17.2 * k} rx={3.6 * k} fill="none" stroke={colors.W} strokeWidth={2.8 * k} style={style} />
          ) : (
            <rect key={`${r}${c}`} x={x} y={y} width={20 * k} height={20 * k} rx={5 * k} fill={colors[s as 'A']} style={style} />
          );
        }),
      )}
    </>
  );
};

/** Official lockup: cells build up one by one, then the wordmark from the SVG file wipes in. */
const Lockup: React.FC<{w: number; delay?: number; style?: React.CSSProperties}> = ({w, delay = -999, style}) => {
  const dark = React.useContext(Dark);
  const p = useIn(delay + 40);
  return (
    <div style={{position: 'relative', width: w, height: (w * 220) / 1020, ...style}}>
      <Img
        src={dark ? lockupNegatyw : lockupKolor}
        style={{position: 'absolute', inset: 0, width: w, clipPath: `inset(0 ${(1 - p) * 77}% 0 23%)`}}
      />
      <svg viewBox="-30 -10 1020 220" width={w} style={{position: 'absolute', inset: 0}}>
        <MarkCells k={5 / 3} delay={delay} dark={dark} />
      </svg>
    </div>
  );
};

const Browser: React.FC<{
  src: string;
  w: number;
  h: number;
  scroll?: [number, number];
  zoom?: [number, number];
  origin?: string;
  delay?: number;
  style?: React.CSSProperties;
}> = ({src, w, h, scroll = [0, 0], zoom = [1, 1], origin = '50% 0%', delay = 0, style}) => {
  const f = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const p = useIn(delay);
  const t = interpolate(f, [delay + 15, durationInFrames - 15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.quad),
  });
  return (
    <div
      style={{
        width: w,
        borderRadius: 18,
        overflow: 'hidden',
        background: '#fff',
        boxShadow: '0 40px 90px rgba(20,39,78,.28), 0 0 0 2px rgba(20,39,78,.12)',
        opacity: p,
        transform: `translateY(${(1 - p) * 80}px)`,
        ...style,
      }}
    >
      <div style={{height: 44, background: C.cream2, display: 'flex', alignItems: 'center', gap: 9, paddingLeft: 18}}>
        {[C.amber, C.sky, C.navy].map((c) => (
          <div key={c} style={{width: 14, height: 14, borderRadius: 4, background: c}} />
        ))}
        <div style={{marginLeft: 18, height: 26, width: w * 0.5, borderRadius: 13, background: '#fff', color: C.muted, fontSize: 15, lineHeight: '26px', paddingLeft: 14}}>
          dane.gov.pl – prototyp
        </div>
      </div>
      <div style={{height: h, overflow: 'hidden'}}>
        <Img
          src={staticFile(src)}
          style={{
            width: w,
            display: 'block',
            transformOrigin: origin,
            transform: `translateY(${-interpolate(t, [0, 1], scroll)}px) scale(${interpolate(t, [0, 1], zoom)})`,
          }}
        />
      </div>
    </div>
  );
};

const Phone: React.FC<{src: string; w?: number; h?: number; delay?: number; style?: React.CSSProperties; scroll?: number}> = ({
  src,
  w = 380,
  h = 780,
  delay = 0,
  style,
  scroll = 0,
}) => {
  const f = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const p = useIn(delay, 18);
  const t = interpolate(f, [delay + 30, durationInFrames - 20], [0, scroll], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div
      style={{
        width: w,
        height: h,
        borderRadius: 54,
        padding: 14,
        background: C.navy2,
        boxShadow: '0 40px 90px rgba(20,39,78,.35)',
        opacity: Math.min(1, p * 1.5),
        transform: `translateY(${(1 - p) * 240}px) rotate(${(1 - p) * 8}deg)`,
        ...style,
      }}
    >
      <div style={{width: '100%', height: '100%', borderRadius: 42, overflow: 'hidden', background: '#fff'}}>
        <Img src={staticFile(src)} style={{width: '100%', display: 'block', transform: `translateY(${-t}px)`}} />
      </div>
    </div>
  );
};

const Tag: React.FC<{delay: number; color?: string; style?: React.CSSProperties; children: React.ReactNode}> = ({
  delay,
  color = C.navy,
  style,
  children,
}) => (
  <Pop
    delay={delay}
    style={{
      position: 'absolute',
      background: color,
      color: color === C.amber ? C.navy2 : '#fff',
      fontFamily: HEAD,
      fontSize: 28,
      fontWeight: 600,
      padding: '14px 26px',
      borderRadius: 16,
      boxShadow: '0 16px 40px rgba(20,39,78,.3)',
      whiteSpace: 'nowrap',
      ...style,
    }}
  >
    {children}
  </Pop>
);

const Split: React.FC<{left: React.ReactNode; right: React.ReactNode; leftW?: number}> = ({left, right, leftW = 760}) => (
  <AbsoluteFill style={{flexDirection: 'row', alignItems: 'center', padding: '0 110px', gap: 70}}>
    <div style={{width: leftW, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 30}}>{left}</div>
    <div style={{flex: 1, position: 'relative', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{right}</div>
  </AbsoluteFill>
);

const Count: React.FC<{to: number; delay: number; suffix?: string}> = ({to, delay, suffix = ''}) => {
  const f = useCurrentFrame();
  const v = interpolate(f, [delay, delay + 50], [0, to], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  return (
    <>
      {fmt(v)}
      {suffix}
    </>
  );
};

// ---------- scenes ----------

const Hook: React.FC = () => {
  const f = useCurrentFrame();
  const words = 'Defibrylator pomaga tylko wtedy,'.split(' ');
  const line = interpolate(f, [5, 75], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
  const beat = 'h150 l18 -14 l18 14 h34 l14 26 l26 -170 l26 200 l16 -56 h44 l26 -26 l26 26 h82';
  return (
    <Scene bg="navy">
      <svg width={1920} height={400} viewBox="0 -200 1920 400" style={{position: 'absolute', left: 0, top: 110}}>
        <path d={`M-20 0 ${beat} ${beat} ${beat} ${beat}`} fill="none" stroke={C.amber} strokeWidth={6} strokeLinejoin="round" strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - line} />
      </svg>
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', paddingTop: 220, textAlign: 'center'}}>
        <H size={96}>
          {words.map((w, i) => (
            <Rise key={i} delay={30 + i * 5} style={{display: 'inline-block', marginRight: 24}}>
              {w}
            </Rise>
          ))}
          <br />
          <Rise delay={62} style={{display: 'inline-block'}}>
            <Em>gdy wiadomo, gdzie jest.</Em>
          </Rise>
        </H>
        <Rise delay={100} style={{marginTop: 50, fontSize: 42, color: 'rgba(255,255,255,.76)'}}>
          Dziś w Polsce nie ma jednego otwartego zbioru, który to wie.
        </Rise>
      </AbsoluteFill>
    </Scene>
  );
};

const Problem: React.FC = () => {
  const f = useCurrentFrame();
  const cards = [
    {t: `${N.miasta} zbiory miejskie`, s: 'dane.gov.pl · każdy w innym układzie', n: N.miastaRekordy, x: 130, y: 300, r: -4},
    {t: 'API Warszawy', s: 'osobny interfejs, własne pola', n: N.warszawa, x: 700, y: 260, r: 3},
    {t: 'OpenStreetMap', s: 'społeczność · licencja ODbL', n: N.osm, x: 1270, y: 310, r: -3},
  ];
  const zero = useIn(140, 10);
  return (
    <Scene>
      <AbsoluteFill style={{padding: '90px 110px'}}>
        <Rise>
          <Kicker>Problem</Kicker>
        </Rise>
        <Rise delay={8} style={{marginTop: 16}}>
          <H size={76}>Dane są. Tylko każde gdzie indziej.</H>
        </Rise>
      </AbsoluteFill>
      {cards.map((c, i) => {
        const d = 30 + i * 14;
        const p = spring({frame: f - d, fps: 30, config: {damping: 14}});
        return (
          <div
            key={c.t}
            style={{
              position: 'absolute',
              left: c.x,
              top: c.y + Math.sin((f + i * 40) / 25) * 8,
              width: 520,
              padding: 40,
              borderRadius: 28,
              background: C.white,
              border: `2px solid ${C.cream2}`,
              boxShadow: '0 24px 60px rgba(20,39,78,.14)',
              transform: `rotate(${c.r}deg) scale(${p})`,
              opacity: Math.min(1, p * 2),
            }}
          >
            <div style={{fontFamily: HEAD, fontSize: 40, fontWeight: 700}}>{c.t}</div>
            <div style={{fontSize: 26, color: C.muted, marginTop: 6}}>{c.s}</div>
            <div style={{fontFamily: HEAD, fontSize: 96, fontWeight: 700, color: C.blue, marginTop: 14, fontVariantNumeric: 'tabular-nums'}}>
              <Count to={c.n} delay={d + 5} />
            </div>
            <div style={{fontSize: 24, color: C.muted}}>rekordów</div>
          </div>
        );
      })}
      <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 80}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 36, transform: `scale(${zero})`, opacity: Math.min(1, zero * 2)}}>
          <div style={{fontFamily: HEAD, fontSize: 190, fontWeight: 700, color: C.amber, lineHeight: 1}}>{N.potwierdzone}</div>
          <div style={{fontFamily: HEAD, fontSize: 44, fontWeight: 600, lineHeight: 1.25}}>
            z {fmt(N.rejestr)} rekordów
            <br />
            potwierdził ktoś odpowiedzialny za urządzenie
          </div>
        </div>
      </AbsoluteFill>
    </Scene>
  );
};

const Uk: React.FC = () => {
  const items = [
    {n: UK.aed, sfx: '', l: 'defibrylatorów w jednym krajowym rejestrze'},
    {n: UK.guardians, sfx: '', l: 'opiekunów, którzy sami wpisali i utrzymują swoje urządzenia'},
    {n: UK.unknownPct, sfx: '%', l: 'tych urządzeń było wcześniej nieznanych pogotowiu', hot: true},
  ];
  return (
    <Scene bg="navy">
      <AbsoluteFill style={{padding: '90px 110px'}}>
        <Rise>
          <Kicker>Da się · Wielka Brytania, rejestr The Circuit</Kicker>
        </Rise>
        <Rise delay={10} style={{marginTop: 18}}>
          <H size={80}>
            Jeden rejestr. <Em>Każde urządzenie ma opiekuna.</Em>
          </H>
        </Rise>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 40, marginTop: 90}}>
          {items.map((it, i) => {
            const d = 45 + i * 40;
            return (
              <Rise key={it.l} delay={d} style={{borderTop: `6px solid ${it.hot ? C.amber : '#6E97FF'}`, paddingTop: 26}}>
                <div style={{fontFamily: HEAD, fontSize: 150, fontWeight: 700, color: it.hot ? C.amber : C.white, fontVariantNumeric: 'tabular-nums', letterSpacing: -4, lineHeight: 1.05}}>
                  <Count to={it.n} delay={d} suffix={it.sfx} />
                </div>
                <div style={{fontSize: 34, lineHeight: 1.3, color: 'rgba(255,255,255,.8)', marginTop: 10}}>{it.l}</div>
              </Rise>
            );
          })}
        </div>
        <Rise delay={185} style={{marginTop: 80}}>
          <H size={54}>
            Te urządzenia już wisiały na ścianach. <Em>Brakowało jednego miejsca i zaproszenia.</Em>
          </H>
        </Rise>
        <Rise delay={215} style={{marginTop: 22, fontSize: 32, color: 'rgba(255,255,255,.8)'}}>
          Rejestr urósł dzięki kampanii: e-maile do partnerów, strona akcji, media społecznościowe. Korzysta z niego wszystkie {UK.services} służb pogotowia.
        </Rise>
      </AbsoluteFill>
      <div style={{position: 'absolute', left: 110, bottom: 44, fontSize: 22, color: 'rgba(255,255,255,.6)'}}>
        Źródło: O’Sullivan i in., „Resuscitation Plus” 2024 · stan na 31.12.2023
      </div>
    </Scene>
  );
};

const Insight: React.FC = () => {
  const cards = [
    {t: 'Łatwa obsługa', s: 'Plik albo formularz. Skan kodu QR telefonem. Bez instalowania aplikacji.'},
    {t: 'Dobrze rozpropagowana akcja', s: 'Nazwa, znak i konkretna korzyść dla każdego, kto dba o swoje urządzenie.'},
  ];
  return (
    <Scene>
      <AbsoluteFill style={{padding: '100px 110px', alignItems: 'center', textAlign: 'center'}}>
        <Rise>
          <H size={84}>
            To nie jest problem technologii.
            <br />
            <Em>Potrzeba dwóch rzeczy.</Em>
          </H>
        </Rise>
        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 44, marginTop: 80, width: '100%', textAlign: 'left'}}>
          {cards.map((c, i) => (
            <Pop key={c.t} delay={45 + i * 30} style={{background: C.white, borderRadius: 28, padding: 54, boxShadow: '0 24px 60px rgba(20,39,78,.14)', borderTop: `10px solid ${i ? C.amber : C.blue}`}}>
              <div style={{fontFamily: HEAD, fontSize: 30, fontWeight: 600, color: C.muted}}>{i + 1}</div>
              <div style={{fontFamily: HEAD, fontSize: 58, fontWeight: 700, marginTop: 6, letterSpacing: '-0.03em'}}>{c.t}</div>
              <div style={{fontSize: 34, lineHeight: 1.35, color: C.muted, marginTop: 16}}>{c.s}</div>
            </Pop>
          ))}
        </div>
        <Rise delay={125} style={{marginTop: 60, fontFamily: HEAD, fontSize: 46, fontWeight: 600}}>
          Jedno i drugie daje nasza akcja.
        </Rise>
      </AbsoluteFill>
    </Scene>
  );
};

const Brand: React.FC = () => {
  const chips: [keyof typeof STATE.light, string][] = [
    ['A', 'zweryfikowany'],
    ['Z', 'zgłoszony'],
    ['U', 'niepotwierdzony'],
    ['N', 'nieaktualny'],
    ['W', 'wycofany'],
  ];
  return (
    <Scene bg="white">
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
        <Lockup w={1300} delay={12} />
        <Rise delay={75} style={{marginTop: 30}}>
          <H size={64}>
            Dbasz o AED? <Em>Pokaż to w danych.</Em>
          </H>
        </Rise>
        <Rise delay={105} style={{marginTop: 60, fontSize: 32, color: C.muted}}>
          Każda komórka znaku to jedno urządzenie. Kolor mówi, w jakim stanie są jego dane.
        </Rise>
        <div style={{display: 'flex', gap: 36, marginTop: 30}}>
          {chips.map(([k, label], i) => (
            <Pop key={k} delay={120 + i * 8} style={{display: 'flex', alignItems: 'center', gap: 14, fontSize: 30, fontWeight: 700}}>
              <div
                style={{
                  width: 34,
                  height: 34,
                  borderRadius: 9,
                  boxSizing: 'border-box',
                  background: k === 'W' ? 'transparent' : STATE.light[k],
                  border: k === 'W' ? `5px solid ${C.grey}` : 0,
                }}
              />
              {label}
            </Pop>
          ))}
        </div>
      </AbsoluteFill>
    </Scene>
  );
};

const Step1: React.FC = () => (
  <Scene>
    <Split
      left={
        <>
          <Rise>
            <Kicker>Krok 1 · Sprzedawca</Kicker>
          </Rise>
          <Rise delay={8}>
            <H>
              Firma zgłasza AED <Em>przy sprzedaży</Em>
            </H>
          </Rise>
          <Bullet delay={35}>Plik CSV albo formularz – z konta firmy</Bullet>
          <Bullet delay={55}>Raport błędów po polsku, wiersz po wierszu</Bullet>
          <Bullet delay={75}>Każde urządzenie dostaje identyfikator i naklejkę QR</Bullet>
        </>
      }
      right={
        <>
          <Browser src="02-panel-firmy-raport-walidacji-csv.png" w={900} h={600} zoom={[1, 1.22]} origin="20% 30%" delay={15} />
          <Tag delay={90} style={{right: -20, top: 800}}>
            Portal sam mówi, co poprawić
          </Tag>
        </>
      }
    />
  </Scene>
);

const Step2: React.FC = () => {
  const f = useCurrentFrame();
  const p = useIn(15, 14);
  const scan = interpolate(f % 50, [0, 50], [0, 1]);
  const scanOn = f > 35 && f < 105;
  const slide = useIn(100);
  return (
    <Scene>
      <Split
        left={
          <>
            <Rise>
              <Kicker>Krok 2 · Zarządca</Kicker>
            </Rise>
            <Rise delay={8}>
              <H>
                Skanuje naklejkę. <Em>Potwierdza.</Em>
              </H>
            </Rise>
            <Bullet delay={45}>Naklejka z kodem QR jedzie razem z urządzeniem</Bullet>
            <Bullet delay={110}>Lokalizacja z telefonu, godziny dostępu, stan</Bullet>
            <Bullet delay={130}>Trzy kroki na telefonie – bez instalowania aplikacji</Bullet>
          </>
        }
        right={
          <>
            <div
              style={{
                position: 'absolute',
                left: 60 - slide * 60,
                top: 250,
                width: 360,
                borderRadius: 24,
                overflow: 'hidden',
                boxShadow: '0 40px 90px rgba(20,39,78,.3)',
                transform: `scale(${p * (1.15 - slide * 0.2)}) rotate(${-6 + (1 - p) * -20}deg)`,
              }}
            >
              <Img src={staticFile('03-naklejka-qr.png')} style={{width: 360, display: 'block'}} />
              {scanOn && <div style={{position: 'absolute', left: 40, right: 40, top: 130 + scan * 250, height: 6, background: C.blue, boxShadow: `0 0 30px 8px ${C.sky}`}} />}
            </div>
            <Phone src="04-ekran-qr-dysponent-390px.png" delay={100} scroll={110} style={{position: 'absolute', right: 40, top: 150}} />
            <Tag delay={150} style={{right: 0, top: 110, fontSize: 32}}>
              ✓ Zweryfikowany
            </Tag>
          </>
        }
      />
    </Scene>
  );
};

const Step3: React.FC = () => {
  const f = useCurrentFrame();
  const src = ['Samorządy', 'Instytucje', 'Firmy'];
  const flow = (i: number) => ((f + i * 12) % 36) / 36;
  return (
    <Scene>
      <Split
        leftW={800}
        left={
          <>
            <Rise>
              <Kicker>Krok 3 · Portal</Kicker>
            </Rise>
            <Rise delay={8}>
              <H size={76}>
                dane.gov.pl scala wykazy w <Em>Krajowy wykaz AED</Em>
              </H>
            </Rise>
            <Rise delay={30} style={{display: 'flex', alignItems: 'center', gap: 26, marginTop: 10}}>
              <div style={{display: 'flex', flexDirection: 'column', gap: 14}}>
                {src.map((s, i) => (
                  <Pop key={s} delay={40 + i * 8} style={{background: C.white, border: `2px solid ${C.cream2}`, borderRadius: 16, padding: '12px 24px', fontFamily: HEAD, fontSize: 30, fontWeight: 600}}>
                    {s}
                  </Pop>
                ))}
              </div>
              <div style={{position: 'relative', width: 120, height: 180}}>
                {src.map((s, i) => (
                  <div
                    key={s}
                    style={{
                      position: 'absolute',
                      left: flow(i) * 110,
                      top: 24 + i * 62 + (90 - (24 + i * 62)) * flow(i),
                      width: 16,
                      height: 16,
                      borderRadius: 5,
                      background: C.amber,
                      opacity: f > 65 ? 1 - flow(i) * 0.4 : 0,
                    }}
                  />
                ))}
              </div>
              <Pop delay={70} style={{background: C.navy, color: C.white, borderRadius: 22, padding: '24px 30px', fontFamily: HEAD, fontSize: 30, fontWeight: 600, lineHeight: 1.35}}>
                walidacja
                <br />
                deduplikacja
                <br />
                publikacja
              </Pop>
            </Rise>
            <Bullet delay={95}>Ten sam mechanizm, którym portal scala już wykazy DGA</Bullet>
            <Bullet delay={115}>Tabela, mapa i API – odczyt bez logowania</Bullet>
          </>
        }
        right={<Browser src="portal-07-mapa.png" w={860} h={600} scroll={[60, 170]} delay={25} />}
      />
    </Scene>
  );
};

// Heart built from cells: every contributor adds devices, confirmations turn them navy.
const HEART = (() => {
  const out: {x: number; y: number; i: number}[] = [];
  const cols = 19;
  const rows = 17;
  for (let r = 0; r < rows; r++)
    for (let c = 0; c < cols; c++) {
      const x = ((c + 0.5) / cols) * 2.6 - 1.3;
      const y = 1.3 - ((r + 0.5) / rows) * 2.4;
      if ((x * x + y * y - 1) ** 3 - x * x * y ** 3 <= 0) out.push({x: c, y: r, i: out.length});
    }
  return out;
})();

const Together: React.FC = () => {
  const f = useCurrentFrame();
  const who = ['samorząd', 'firma', 'szkoła', 'wspólnota', 'sklep', 'urząd'];
  return (
    <Scene>
      <Split
        leftW={860}
        left={
          <>
            <Rise>
              <Kicker>Wspólna baza</Kicker>
            </Rise>
            <Rise delay={8}>
              <H size={80}>
                Każdy dokłada swoją część. <Em>Każde potwierdzenie poprawia dane wszystkim.</Em>
              </H>
            </Rise>
            <div style={{display: 'flex', flexWrap: 'wrap', gap: 14, marginTop: 6}}>
              {who.map((w, i) => (
                <Pop key={w} delay={50 + i * 10} style={{background: C.white, border: `2px solid ${C.cream2}`, borderRadius: 14, padding: '10px 22px', fontFamily: HEAD, fontSize: 30, fontWeight: 600}}>
                  {w}
                </Pop>
              ))}
            </div>
            <Rise delay={150} style={{fontSize: 38, lineHeight: 1.3, color: C.muted}}>
              Nikt nie musi zbierać wszystkiego sam. Wystarczy, że każdy zadba o swoje urządzenie.
            </Rise>
          </>
        }
        right={
          <div style={{position: 'relative', width: 19 * 38, height: 17 * 38}}>
            {HEART.map(({x, y, i}) => {
              const d = 15 + random(`d${i}`) * 110;
              const p = spring({frame: f - d, fps: 30, config: {damping: 11}});
              const kind = random(`k${i}`);
              const confirmed = f > d + 30 + random(`c${i}`) * 80;
              const bg = !confirmed ? C.sky : kind < 0.06 ? C.amber : kind < 0.16 ? C.blue : C.navy;
              return <div key={i} style={{position: 'absolute', left: x * 38, top: y * 38, width: 32, height: 32, borderRadius: 8, background: bg, transform: `scale(${p})`}} />;
            })}
          </div>
        }
      />
    </Scene>
  );
};

const ICONS: Record<string, React.ReactNode> = {
  pin: <path d="M24 4c-8 0-14 6-14 14 0 10 14 26 14 26s14-16 14-26c0-8-6-14-14-14zm0 19a5 5 0 110-10 5 5 0 010 10z" />,
  badge: <path d="M24 3l6 5 8-1 1 8 6 5-4 7 1 8-8 1-5 7-5-4-8 2-2-8-7-4 4-7-2-8 8-2 3-7zM17 24l5 5 10-11-3-3-7 8-2-2z" />,
  table: <path d="M5 8h38v32H5zM9 16v6h12v-6zm16 0v6h14v-6zM9 26v6h12v-6zm16 0v6h14v-6z" fillRule="evenodd" />,
  api: <path d="M24 5c10 0 18 3 18 7s-8 7-18 7S6 16 6 12s8-7 18-7zM6 18c0 4 8 7 18 7s18-3 18-7v8c0 4-8 7-18 7S6 30 6 26zm0 14c0 4 8 7 18 7s18-3 18-7v6c0 4-8 7-18 7S6 42 6 38z" />,
};

const Benefits: React.FC = () => {
  const f = useCurrentFrame();
  const cards = [
    {i: 'badge', c: C.amber, t: 'Firmy i zarządcy', s: 'Odznaka Opiekuna AED, miejsce na mapie sprzedawców i przypomnienia o terminie baterii i elektrod.'},
    {i: 'table', c: C.blue, t: 'Samorządy', s: 'Jeden wzorzec zamiast własnych tabel. Portal sam sprawdza wykaz i wskazuje, co poprawić.'},
    {i: 'pin', c: C.navy, t: 'Mieszkańcy i ratownicy', s: 'Wiadomo, gdzie jest najbliższy AED, kiedy jest dostępny i kto potwierdził dane.'},
    {i: 'api', c: C.sky, t: 'Państwo i twórcy usług', s: 'Jeden otwarty, aktualny zbiór z API – gotowy do map, nawigacji i aplikacji.'},
  ];
  return (
    <Scene>
      <AbsoluteFill style={{padding: '80px 110px'}}>
        <Rise>
          <Kicker>Co z tego masz</Kicker>
        </Rise>
        <Rise delay={8} style={{marginTop: 12}}>
          <H size={80}>
            Dajesz dane. <Em>Dostajesz coś w zamian.</Em>
          </H>
        </Rise>
        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 34, marginTop: 64}}>
          {cards.map((c, i) => {
            const d = 35 + i * 26;
            const p = spring({frame: f - d, fps: 30, config: {damping: 16}});
            return (
              <div
                key={c.t}
                style={{
                  display: 'flex',
                  gap: 30,
                  padding: 44,
                  borderRadius: 28,
                  background: C.white,
                  borderLeft: `12px solid ${c.c}`,
                  boxShadow: '0 24px 60px rgba(20,39,78,.12)',
                  opacity: Math.min(1, p * 2),
                  transform: `translateY(${(1 - p) * 90}px)`,
                }}
              >
                <svg width={80} height={80} viewBox="0 0 48 48" fill={c.c} style={{flexShrink: 0}}>
                  {ICONS[c.i]}
                </svg>
                <div>
                  <div style={{fontFamily: HEAD, fontSize: 42, fontWeight: 700}}>{c.t}</div>
                  <div style={{fontSize: 31, lineHeight: 1.35, color: C.muted, marginTop: 10}}>{c.s}</div>
                </div>
              </div>
            );
          })}
        </div>
        <Rise delay={160} style={{marginTop: 40, fontFamily: HEAD, fontSize: 38, fontWeight: 600, textAlign: 'center'}}>
          Im więcej opiekunów, tym pełniejsza mapa.
        </Rise>
      </AbsoluteFill>
    </Scene>
  );
};

const Numbers: React.FC = () => {
  const items = [
    {n: N.zrodla, l: 'źródeł sprowadzonych do jednego standardu'},
    {n: N.rejestr, l: 'rekordów w rejestrze po mapowaniu'},
    {n: N.polaczenia, l: 'duplikatów połączonych automatycznie'},
    {n: N.eksport, l: 'rekordów gotowych do publikacji na dane.gov.pl'},
  ];
  return (
    <Scene bg="navy">
      <AbsoluteFill style={{padding: '90px 110px'}}>
        <Rise>
          <Kicker>Działa już dziś – na prawdziwych danych</Kicker>
        </Rise>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 30, marginTop: 200}}>
          {items.map((it, i) => {
            const d = 15 + i * 16;
            return (
              <Rise key={it.l} delay={d} style={{borderTop: `6px solid ${i === 3 ? C.amber : '#6E97FF'}`, paddingTop: 26}}>
                <div style={{fontFamily: HEAD, fontSize: 120, fontWeight: 700, color: i === 3 ? C.amber : C.white, fontVariantNumeric: 'tabular-nums', letterSpacing: -3}}>
                  <Count to={it.n} delay={d} />
                </div>
                <div style={{fontSize: 32, lineHeight: 1.3, color: 'rgba(255,255,255,.8)', marginTop: 8}}>{it.l}</div>
              </Rise>
            );
          })}
        </div>
        <Rise delay={105} style={{marginTop: 110, textAlign: 'center'}}>
          <H size={48}>
            To stan początkowy. <Em>Resztę uzupełniają ci, którzy opiekują się urządzeniami.</Em>
          </H>
        </Rise>
      </AbsoluteFill>
    </Scene>
  );
};

const Cta: React.FC = () => (
  <Scene bg="white">
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', textAlign: 'center'}}>
      <Lockup w={900} delay={8} />
      <Pop delay={60} style={{marginTop: 50}}>
        <H size={120}>
          Zbudujmy tę bazę <Em>razem.</Em>
        </H>
      </Pop>
      <Rise delay={90} style={{fontFamily: HEAD, fontSize: 52, marginTop: 30, fontWeight: 600}}>
        Dbasz o AED? Pokaż to w danych.
      </Rise>
      <Rise delay={120} style={{marginTop: 70, fontSize: 28, color: C.muted, letterSpacing: 2}}>
        MISJA AED – DANE NA RATUNEK · HACKNATION 2026 · PROTOTYP
      </Rise>
    </AbsoluteFill>
  </Scene>
);

export const Pitch: React.FC = () => (
  <AbsoluteFill style={{fontFamily: BODY, color: C.navy, background: C.cream}}>
    <Series>
      <Series.Sequence durationInFrames={SCENES.hook}><Hook /></Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.problem}><Problem /></Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.uk}><Uk /></Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.insight}><Insight /></Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.brand}><Brand /></Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.step1}><Step1 /></Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.step2}><Step2 /></Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.step3}><Step3 /></Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.together}><Together /></Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.benefits}><Benefits /></Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.numbers}><Numbers /></Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.cta}><Cta /></Series.Sequence>
    </Series>
  </AbsoluteFill>
);
