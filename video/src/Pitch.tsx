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
import {loadFont} from '@remotion/google-fonts/Roboto';
// Numbers on screen come only from our own report (CLAUDE.md, hard rule 10).
import raport from '../../datasets/out/raport.json';

const {fontFamily} = loadFont('normal', {
  weights: ['400', '700', '900'],
  subsets: ['latin', 'latin-ext'],
});

const C = {
  navy: '#0a1d3a',
  blue: '#0b62c8',
  sky: '#6fb6ff',
  red: '#e0243f',
  yellow: '#ffc400',
  green: '#1faa59',
  white: '#ffffff',
  dim: 'rgba(255,255,255,.72)',
};

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
  potwierdzone: N_potwierdzone(),
};
function N_potwierdzone() {
  const s = raport.statusy as Record<string, number>;
  return s.aktywny ?? 0;
}

const fmt = (n: number) =>
  Math.round(n)
    .toString()
    .replace(/\B(?=(\d{3})+(?!\d))/g, ' ');

const SCENES = {
  hook: 165,
  problem: 240,
  solution: 135,
  step1: 210,
  step2: 240,
  step3: 225,
  citizen: 165,
  benefits: 285,
  numbers: 195,
  cta: 210,
};
export const TOTAL = Object.values(SCENES).reduce((a, b) => a + b, 0);

// ---------- helpers ----------

const useIn = (delay = 0, damping = 200) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: frame - delay, fps, config: {damping}});
};

const Rise: React.FC<{
  delay?: number;
  y?: number;
  x?: number;
  style?: React.CSSProperties;
  children: React.ReactNode;
}> = ({delay = 0, y = 40, x = 0, style, children}) => {
  const p = useIn(delay);
  return (
    <div
      style={{
        opacity: p,
        transform: `translate(${(1 - p) * x}px, ${(1 - p) * y}px)`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

const Pop: React.FC<{delay?: number; style?: React.CSSProperties; children: React.ReactNode}> = ({
  delay = 0,
  style,
  children,
}) => {
  const p = useIn(delay, 12);
  return <div style={{transform: `scale(${p})`, opacity: Math.min(1, p * 2), ...style}}>{children}</div>;
};

const Scene: React.FC<{children: React.ReactNode}> = ({children}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const o = interpolate(frame, [0, 12, durationInFrames - 12, durationInFrames], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const s = interpolate(frame, [0, durationInFrames], [1, 1.03]);
  return <AbsoluteFill style={{opacity: o, transform: `scale(${s})`}}>{children}</AbsoluteFill>;
};

const Bg: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(1300px 900px at ${50 + 12 * Math.sin(f / 110)}% ${
          30 + 8 * Math.cos(f / 140)
        }%, #154a8c 0%, ${C.navy} 55%, #050d1c 100%)`,
      }}
    >
      <AbsoluteFill
        style={{
          backgroundImage:
            'linear-gradient(rgba(255,255,255,.045) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.045) 1px, transparent 1px)',
          backgroundSize: '80px 80px',
          backgroundPosition: `${-f * 0.4}px ${-f * 0.2}px`,
        }}
      />
    </AbsoluteFill>
  );
};

const BEAT = 'h150 l18 -14 l18 14 h34 l14 26 l26 -170 l26 200 l16 -56 h44 l26 -26 l26 26 h82';
const Ecg: React.FC<{y: number; delay?: number; dur?: number; opacity?: number}> = ({
  y,
  delay = 0,
  dur = 70,
  opacity = 1,
}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [delay, delay + dur], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.cubic),
  });
  return (
    <svg
      width={1920}
      height={400}
      viewBox="0 -200 1920 400"
      style={{position: 'absolute', left: 0, top: y - 200, opacity, filter: `drop-shadow(0 0 14px ${C.red})`}}
    >
      <path
        d={`M-20 0 ${BEAT} ${BEAT} ${BEAT} ${BEAT}`}
        fill="none"
        stroke={C.red}
        strokeWidth={6}
        strokeLinejoin="round"
        strokeLinecap="round"
        pathLength={1}
        strokeDasharray={1}
        strokeDashoffset={1 - p}
      />
    </svg>
  );
};

const Kicker: React.FC<{children: React.ReactNode; color?: string}> = ({children, color = C.yellow}) => (
  <div style={{fontSize: 30, fontWeight: 700, letterSpacing: 5, color, textTransform: 'uppercase'}}>
    {children}
  </div>
);

const H: React.FC<{children: React.ReactNode; size?: number; style?: React.CSSProperties}> = ({
  children,
  size = 84,
  style,
}) => (
  <div style={{fontSize: size, fontWeight: 900, lineHeight: 1.08, letterSpacing: -1.5, ...style}}>
    {children}
  </div>
);

const Em: React.FC<{children: React.ReactNode; color?: string}> = ({children, color = C.yellow}) => (
  <span style={{color}}>{children}</span>
);

const Bullet: React.FC<{delay: number; children: React.ReactNode}> = ({delay, children}) => (
  <Rise delay={delay} y={0} x={-40} style={{display: 'flex', gap: 22, alignItems: 'flex-start'}}>
    <div
      style={{
        marginTop: 9,
        width: 30,
        height: 30,
        borderRadius: 15,
        background: C.green,
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <svg width={18} height={18} viewBox="0 0 18 18">
        <path d="M3 9.5 7.2 13.5 15 5" fill="none" stroke="#fff" strokeWidth={3} strokeLinecap="round" />
      </svg>
    </div>
    <div style={{fontSize: 38, lineHeight: 1.3, color: C.dim}}>{children}</div>
  </Rise>
);

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
        boxShadow: '0 40px 120px rgba(0,0,0,.55), 0 0 0 1px rgba(255,255,255,.15)',
        opacity: p,
        transform: `perspective(2200px) rotateY(${(1 - p) * -18 - 4}deg) rotateX(2deg) translateY(${
          (1 - p) * 80
        }px)`,
        ...style,
      }}
    >
      <div style={{height: 44, background: '#e7ebf1', display: 'flex', alignItems: 'center', gap: 9, paddingLeft: 18}}>
        {['#ff5f57', '#febc2e', '#28c840'].map((c) => (
          <div key={c} style={{width: 14, height: 14, borderRadius: 7, background: c}} />
        ))}
        <div
          style={{
            marginLeft: 18,
            height: 26,
            width: w * 0.5,
            borderRadius: 13,
            background: '#fff',
            color: '#5b6676',
            fontSize: 15,
            lineHeight: '26px',
            paddingLeft: 14,
          }}
        >
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
  const t = interpolate(f, [delay + 30, durationInFrames - 20], [0, scroll], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <div
      style={{
        width: w,
        height: h,
        borderRadius: 54,
        padding: 14,
        background: '#10151d',
        boxShadow: '0 40px 120px rgba(0,0,0,.6), 0 0 0 2px rgba(255,255,255,.18)',
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
  color = C.yellow,
  style,
  children,
}) => (
  <Pop
    delay={delay}
    style={{
      position: 'absolute',
      background: color,
      color: color === C.yellow ? '#111' : '#fff',
      fontSize: 30,
      fontWeight: 700,
      padding: '14px 26px',
      borderRadius: 40,
      boxShadow: '0 16px 40px rgba(0,0,0,.4)',
      whiteSpace: 'nowrap',
      ...style,
    }}
  >
    {children}
  </Pop>
);

const Split: React.FC<{left: React.ReactNode; right: React.ReactNode; leftW?: number}> = ({
  left,
  right,
  leftW = 760,
}) => (
  <AbsoluteFill style={{flexDirection: 'row', alignItems: 'center', padding: '0 110px', gap: 70}}>
    <div style={{width: leftW, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 30}}>{left}</div>
    <div style={{flex: 1, position: 'relative', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      {right}
    </div>
  </AbsoluteFill>
);

// ---------- scenes ----------

const Hook: React.FC = () => {
  const words = 'Defibrylator pomaga tylko wtedy,'.split(' ');
  return (
    <Scene>
      <Ecg y={310} delay={5} />
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
        <Rise delay={105} style={{marginTop: 50, fontSize: 42, color: C.dim}}>
          Dziś w Polsce nie ma jednego otwartego zbioru, który to wie.
        </Rise>
      </AbsoluteFill>
    </Scene>
  );
};

const Problem: React.FC = () => {
  const f = useCurrentFrame();
  const cards = [
    {t: `${N.miasta} zbiory miejskie`, s: 'dane.gov.pl · każdy w innym układzie', n: N.miastaRekordy, x: 130, y: 300, r: -5},
    {t: 'API Warszawy', s: 'osobny interfejs, własne pola', n: N.warszawa, x: 700, y: 250, r: 3},
    {t: 'OpenStreetMap', s: 'społeczność · licencja ODbL', n: N.osm, x: 1270, y: 310, r: -3},
  ];
  const zero = useIn(140, 10);
  return (
    <Scene>
      <AbsoluteFill style={{padding: '90px 110px'}}>
        <Rise>
          <Kicker color={C.red}>Problem</Kicker>
        </Rise>
        <Rise delay={8} style={{marginTop: 16}}>
          <H size={76}>Dane są. Tylko każde gdzie indziej.</H>
        </Rise>
      </AbsoluteFill>
      {cards.map((c, i) => {
        const d = 30 + i * 14;
        const p = spring({frame: f - d, fps: 30, config: {damping: 14}});
        const n = interpolate(f, [d + 5, d + 50], [0, c.n], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
          easing: Easing.out(Easing.cubic),
        });
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
              background: 'rgba(255,255,255,.08)',
              border: '1px solid rgba(255,255,255,.22)',
              backdropFilter: 'blur(8px)',
              transform: `rotate(${c.r}deg) scale(${p})`,
              opacity: Math.min(1, p * 2),
            }}
          >
            <div style={{fontSize: 40, fontWeight: 700}}>{c.t}</div>
            <div style={{fontSize: 26, color: C.dim, marginTop: 6}}>{c.s}</div>
            <div style={{fontSize: 96, fontWeight: 900, color: C.sky, marginTop: 14}}>{fmt(n)}</div>
            <div style={{fontSize: 24, color: C.dim}}>rekordów</div>
          </div>
        );
      })}
      <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 90}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 36, transform: `scale(${zero})`, opacity: Math.min(1, zero * 2)}}>
          <div style={{fontSize: 190, fontWeight: 900, color: C.red, lineHeight: 1}}>{N.potwierdzone}</div>
          <div style={{fontSize: 46, fontWeight: 700, lineHeight: 1.2}}>
            z {fmt(N.rejestr)} rekordów
            <br />
            potwierdził ktoś odpowiedzialny za urządzenie
          </div>
        </div>
      </AbsoluteFill>
    </Scene>
  );
};

const Solution: React.FC = () => {
  const f = useCurrentFrame();
  const ring = (d: number) => {
    const t = ((f + d) % 60) / 60;
    return (
      <div
        key={d}
        style={{
          position: 'absolute',
          width: 300 + t * 1300,
          height: 300 + t * 1300,
          borderRadius: '50%',
          border: `3px solid ${C.sky}`,
          opacity: (1 - t) * 0.35,
        }}
      />
    );
  };
  return (
    <Scene>
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>{[0, 20, 40].map(ring)}</AbsoluteFill>
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', textAlign: 'center', gap: 6}}>
        {['Jeden standard.', 'Jeden rejestr.'].map((t, i) => (
          <Pop key={t} delay={8 + i * 18}>
            <H size={120}>{t}</H>
          </Pop>
        ))}
        <Pop delay={46}>
          <H size={120}>
            <Em>Na dane.gov.pl.</Em>
          </H>
        </Pop>
        <Rise delay={70} style={{fontSize: 40, color: C.dim, marginTop: 34}}>
          Dane wprowadza ten, kto za urządzenie odpowiada. Publikuje ministerstwo.
        </Rise>
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
          <Bullet delay={40}>Plik CSV albo formularz – z konta firmy</Bullet>
          <Bullet delay={60}>Raport błędów po polsku, wiersz po wierszu</Bullet>
          <Bullet delay={80}>Każde urządzenie dostaje identyfikator i naklejkę QR</Bullet>
        </>
      }
      right={
        <>
          <Browser src="02-panel-firmy-raport-walidacji-csv.png" w={900} h={600} zoom={[1, 1.22]} origin="20% 30%" delay={15} />
          <Tag delay={95} style={{right: -20, top: 800}}>
            Walidacja zanim cokolwiek trafi do rejestru
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
  const scanOn = f > 40 && f < 125;
  const slide = useIn(120);
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
            <Bullet delay={50}>Naklejka z kodem QR jedzie razem z urządzeniem</Bullet>
            <Bullet delay={135}>Lokalizacja z telefonu, godziny dostępu, stan</Bullet>
            <Bullet delay={160}>Trzy kroki, około minuty – bez instalowania aplikacji</Bullet>
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
                boxShadow: '0 40px 100px rgba(0,0,0,.55)',
                transform: `scale(${p * (1.15 - slide * 0.2)}) rotate(${-6 + (1 - p) * -20}deg)`,
              }}
            >
              <Img src={staticFile('03-naklejka-qr.png')} style={{width: 360, display: 'block'}} />
              {scanOn && (
                <div
                  style={{
                    position: 'absolute',
                    left: 40,
                    right: 40,
                    top: 130 + scan * 250,
                    height: 6,
                    background: C.green,
                    boxShadow: `0 0 30px 8px ${C.green}`,
                  }}
                />
              )}
            </div>
            <Phone src="04-ekran-qr-dysponent-390px.png" delay={120} scroll={110} style={{position: 'absolute', right: 40, top: 150}} />
            <Tag delay={185} color={C.green} style={{right: 0, top: 110, fontSize: 34}}>
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
            <Rise delay={35} style={{display: 'flex', alignItems: 'center', gap: 26, marginTop: 10}}>
              <div style={{display: 'flex', flexDirection: 'column', gap: 14}}>
                {src.map((s, i) => (
                  <Pop key={s} delay={45 + i * 8} style={{background: 'rgba(255,255,255,.1)', border: '1px solid rgba(255,255,255,.25)', borderRadius: 16, padding: '12px 24px', fontSize: 30, fontWeight: 700}}>
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
                      width: 14,
                      height: 14,
                      borderRadius: 7,
                      background: C.yellow,
                      opacity: f > 70 ? 1 - flow(i) * 0.4 : 0,
                    }}
                  />
                ))}
              </div>
              <Pop delay={80} style={{background: C.blue, borderRadius: 22, padding: '24px 30px', fontSize: 30, fontWeight: 700, lineHeight: 1.35, boxShadow: `0 0 60px ${C.blue}`}}>
                walidacja
                <br />
                deduplikacja
                <br />
                publikacja
              </Pop>
            </Rise>
            <Bullet delay={110}>Ten sam mechanizm, którym portal scala już wykazy DGA</Bullet>
            <Bullet delay={130}>Tabela, mapa i API – odczyt bez logowania</Bullet>
          </>
        }
        right={
          <Browser src="portal-07-mapa.png" w={860} h={600} scroll={[60, 170]} delay={25} />
        }
      />
    </Scene>
  );
};

const Citizen: React.FC = () => (
  <Scene>
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
      <Browser src="10-mapa-kraj.png" w={1240} h={620} zoom={[1.05, 1.25]} origin="50% 60%" style={{position: 'absolute', left: 90, top: 340}} />
      <Phone src="12-najblizszy-aed-390px.png" delay={35} scroll={260} w={350} h={720} style={{position: 'absolute', right: 150, top: 310}} />
    </AbsoluteFill>
    <AbsoluteFill style={{padding: '70px 110px'}}>
      <Rise>
        <Kicker>Efekt</Kicker>
      </Rise>
      <Rise delay={8} style={{marginTop: 12}}>
        <H size={72}>
          Każdy widzi <Em>najbliższy AED</Em> – i to, czy dane ktoś potwierdził
        </H>
      </Rise>
    </AbsoluteFill>
  </Scene>
);

const ICONS: Record<string, React.ReactNode> = {
  pin: <path d="M24 4c-8 0-14 6-14 14 0 10 14 26 14 26s14-16 14-26c0-8-6-14-14-14zm0 19a5 5 0 110-10 5 5 0 010 10z" />,
  badge: <path d="M24 3l6 5 8-1 1 8 6 5-4 7 1 8-8 1-5 7-5-4-8 2-2-8-7-4 4-7-2-8 8-2 3-7zM17 24l5 5 10-11-3-3-7 8-2-2z" />,
  table: <path d="M5 8h38v32H5zM9 16v6h12v-6zm16 0v6h14v-6zM9 26v6h12v-6zm16 0v6h14v-6z" fillRule="evenodd" />,
  api: <path d="M24 5c10 0 18 3 18 7s-8 7-18 7S6 16 6 12s8-7 18-7zM6 18c0 4 8 7 18 7s18-3 18-7v8c0 4-8 7-18 7S6 30 6 26zm0 14c0 4 8 7 18 7s18-3 18-7v6c0 4-8 7-18 7S6 42 6 38z" />,
};

const Benefits: React.FC = () => {
  const f = useCurrentFrame();
  const cards = [
    {i: 'pin', c: C.red, t: 'Mieszkańcy i ratownicy', s: 'Wiadomo, gdzie jest najbliższy AED, kiedy jest dostępny i kto potwierdził dane.'},
    {i: 'badge', c: C.yellow, t: 'Firmy i zarządcy', s: 'Odznaka, miejsce na mapie sprzedawców i przypomnienia o terminie baterii i elektrod.'},
    {i: 'table', c: C.green, t: 'Samorządy', s: 'Jeden wzorzec zamiast własnych tabel. Portal sam sprawdza wykaz i wskazuje, co poprawić.'},
    {i: 'api', c: C.sky, t: 'Państwo i twórcy usług', s: 'Jeden otwarty, aktualny zbiór z API – gotowy do map, nawigacji i aplikacji.'},
  ];
  return (
    <Scene>
      <AbsoluteFill style={{padding: '80px 110px'}}>
        <Rise>
          <Kicker>Co z tego mamy</Kicker>
        </Rise>
        <Rise delay={8} style={{marginTop: 12}}>
          <H size={80}>
            Wspólna baza. <Em>Korzyść dla każdego.</Em>
          </H>
        </Rise>
        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 38, marginTop: 76}}>
          {cards.map((c, i) => {
            const d = 35 + i * 28;
            const p = spring({frame: f - d, fps: 30, config: {damping: 16}});
            const glow = interpolate(f, [d, d + 20, d + 50], [0, 1, 0.25], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
            return (
              <div
                key={c.t}
                style={{
                  display: 'flex',
                  gap: 30,
                  padding: 48,
                  borderRadius: 28,
                  background: 'rgba(255,255,255,.08)',
                  border: `2px solid ${c.c}`,
                  boxShadow: `0 0 ${80 * glow}px ${c.c}`,
                  opacity: Math.min(1, p * 2),
                  transform: `translateY(${(1 - p) * 90}px) scale(${0.9 + p * 0.1})`,
                }}
              >
                <svg width={84} height={84} viewBox="0 0 48 48" fill={c.c} style={{flexShrink: 0}}>
                  {ICONS[c.i]}
                </svg>
                <div>
                  <div style={{fontSize: 44, fontWeight: 900}}>{c.t}</div>
                  <div style={{fontSize: 31, lineHeight: 1.35, color: C.dim, marginTop: 10}}>{c.s}</div>
                </div>
              </div>
            );
          })}
        </div>
        <Rise delay={170} style={{marginTop: 44, fontSize: 38, textAlign: 'center'}}>
          Im więcej dostawców, tym pełniejsza mapa. <Em>Każdy wpis wzmacnia całość.</Em>
        </Rise>
      </AbsoluteFill>
    </Scene>
  );
};

const Numbers: React.FC = () => {
  const f = useCurrentFrame();
  const items = [
    {n: N.zrodla, l: 'źródeł sprowadzonych do jednego standardu'},
    {n: N.rejestr, l: 'rekordów w rejestrze po mapowaniu'},
    {n: N.polaczenia, l: 'duplikatów połączonych automatycznie'},
    {n: N.eksport, l: 'rekordów gotowych do publikacji na dane.gov.pl'},
  ];
  return (
    <Scene>
      <AbsoluteFill style={{padding: '90px 110px'}}>
        <Rise>
          <Kicker>Działa już dziś – na prawdziwych danych</Kicker>
        </Rise>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 30, marginTop: 210}}>
          {items.map((it, i) => {
            const d = 15 + i * 16;
            const v = interpolate(f, [d, d + 55], [0, it.n], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
              easing: Easing.out(Easing.cubic),
            });
            return (
              <Rise key={it.l} delay={d} style={{borderTop: `6px solid ${i === 3 ? C.yellow : C.sky}`, paddingTop: 26}}>
                <div style={{fontSize: 124, fontWeight: 900, color: i === 3 ? C.yellow : C.white, fontVariantNumeric: 'tabular-nums', letterSpacing: -3}}>
                  {fmt(v)}
                </div>
                <div style={{fontSize: 32, lineHeight: 1.3, color: C.dim, marginTop: 8}}>{it.l}</div>
              </Rise>
            );
          })}
        </div>
        <Rise delay={115} style={{marginTop: 110, fontSize: 46, fontWeight: 700, textAlign: 'center'}}>
          To stan początkowy. <Em>Resztę uzupełniają ci, którzy opiekują się urządzeniami.</Em>
        </Rise>
      </AbsoluteFill>
    </Scene>
  );
};

const Cta: React.FC = () => {
  const f = useCurrentFrame();
  const dots = new Array(140).fill(0).map((_, i) => {
    const a = random(`a${i}`) * Math.PI * 2;
    const r = Math.sqrt(random(`r${i}`));
    const d = 10 + random(`d${i}`) * 110;
    const p = spring({frame: f - d, fps: 30, config: {damping: 10}});
    const confirmed = f > d + 40 + random(`c${i}`) * 60;
    return (
      <div
        key={i}
        style={{
          position: 'absolute',
          left: 960 + Math.cos(a) * r * 860,
          top: 540 + Math.sin(a) * r * 470,
          width: 16,
          height: 16,
          borderRadius: 8,
          background: confirmed ? C.green : 'rgba(255,255,255,.45)',
          boxShadow: confirmed ? `0 0 18px ${C.green}` : 'none',
          transform: `scale(${p})`,
        }}
      />
    );
  });
  return (
    <Scene>
      <AbsoluteFill style={{opacity: 0.55}}>{dots}</AbsoluteFill>
      <Ecg y={900} delay={20} dur={110} opacity={0.5} />
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', textAlign: 'center'}}>
        <Pop delay={25}>
          <H size={140}>
            Zbudujmy tę bazę <Em>razem.</Em>
          </H>
        </Pop>
        <Rise delay={60} style={{fontSize: 50, marginTop: 30, fontWeight: 700}}>
          Masz AED? Pokaż go w danych.
        </Rise>
        <Rise delay={95} style={{marginTop: 70, fontSize: 32, color: C.dim, letterSpacing: 2}}>
          MISJA AED – DANE NA RATUNEK · HACKNATION 2026 · PROTOTYP
        </Rise>
      </AbsoluteFill>
    </Scene>
  );
};

export const Pitch: React.FC = () => (
  <AbsoluteFill style={{fontFamily, color: C.white}}>
    <Bg />
    <Series>
      <Series.Sequence durationInFrames={SCENES.hook}><Hook /></Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.problem}><Problem /></Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.solution}><Solution /></Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.step1}><Step1 /></Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.step2}><Step2 /></Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.step3}><Step3 /></Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.citizen}><Citizen /></Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.benefits}><Benefits /></Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.numbers}><Numbers /></Series.Sequence>
      <Series.Sequence durationInFrames={SCENES.cta}><Cta /></Series.Sequence>
    </Series>
  </AbsoluteFill>
);
