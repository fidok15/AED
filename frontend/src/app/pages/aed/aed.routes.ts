import { inject, Provider } from '@angular/core';
import { CanActivateFn, Route, Router } from '@angular/router';
import { LocalizeRouterService } from '@gilsdav/ngx-translate-router';

import { AedApiService } from './aed-api.service';
import { AedCompanyComponent } from './aed-company.component';
import { AedDeviceFormComponent } from './aed-device-form.component';
import { AedMockService } from './aed-mock.service';
import { AedQrComponent } from './aed-qr.component';
import { AedRegistryComponent } from './aed-registry.component';
import { AedComponent } from './aed.component';

// THE SWITCH between the real AED service (docs/api-aed.md, proxied from /api/aed to localhost:8085)
// and mock data. Set to true to work without the service running.
const AED_USE_MOCK = false;

const AED_API: Provider = { provide: AedApiService, useClass: AED_USE_MOCK ? AedMockService : AedApiService };

/** Company pages need a signed-in AED account; the sign-in form is on the panel itself. */
const signedIn: CanActivateFn = () =>
  !!inject(AedApiService).account() ||
  inject(Router).parseUrl(inject(LocalizeRouterService).translateRoute('/!aed/!company') as string);

// Mounted in app-routing.module.ts under `!aed`, inside the portal layout.
export const AED_ROUTES: Route[] = [
  {
    path: '',
    component: AedComponent,
    providers: [AED_API],
    children: [
      { path: '', redirectTo: '!registry', pathMatch: 'full' },
      { path: '!registry', component: AedRegistryComponent },
      { path: '!company', component: AedCompanyComponent },
      { path: '!company/!device', component: AedDeviceFormComponent, canActivate: [signedIn] },
    ],
  },
];

// Mounted under `!aed/!qr`, outside the portal layout: the address printed on the QR sticker,
// /aed/qr/{id_aed}, with `?t=<token>` in the link sent to the site manager.
export const AED_QR_ROUTES: Route[] = [
  {
    path: '',
    component: AedComponent,
    providers: [AED_API],
    data: { app: true },
    children: [{ path: '!:id', component: AedQrComponent }],
  },
];
