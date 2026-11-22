import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {Pitch, TOTAL} from './Pitch';

registerRoot(() =>
  React.createElement(Composition, {
    id: 'Pitch',
    component: Pitch,
    durationInFrames: TOTAL,
    fps: 30,
    width: 1920,
    height: 1080,
  }),
);
