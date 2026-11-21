import { inject } from '@angular/core';
import { CanActivateFn, Route, Router } from '@angular/router';
import { LocalizeRouterService } from '@gilsdav/ngx-translate-router';

import { AedApiService } from './aed-api.service';
import { AedCompanyComponent } from './aed-company.component';
import { AedDeviceFormComponent } from './aed-device-form.component';
import { AedHomeComponent } from './aed-home.component';
import { AedMinistryComponent } from './aed-ministry.component';
import { AedPortalAccountsOffComponent } from './aed-prototype';
import { AedQrComponent } from './aed-qr.component';
import { AedRegistryComponent } from './aed-registry.component';
import { AedSellersComponent } from './aed-sellers.component';
import { AedStickersComponent } from './aed-stickers.component';
import { AedComponent } from './aed.component';

/** Company pages need a signed-in AED account; the sign-in form is on the panel itself. */
const signedIn: CanActivateFn = () =>
  inject(AedApiService).account()?.rola === 'firma' ||
  inject(Router).parseUrl(inject(LocalizeRouterService).translateRoute('/!aed/!company') as string);

// Mounted in app-routing.module.ts under `!aed`, inside the portal layout.
export const AED_ROUTES: Route[] = [
  {
    path: '',
    component: AedComponent,
    providers: [AedApiService],
    children: [
      { path: '', component: AedHomeComponent },
      { path: '!registry', component: AedRegistryComponent },
      { path: '!company', component: AedCompanyComponent },
      { path: '!company/!device', component: AedDeviceFormComponent, canActivate: [signedIn] },
      { path: '!company/!stickers', component: AedStickersComponent, canActivate: [signedIn] },
      { path: '!ministry', component: AedMinistryComponent },
      { path: '!sellers', component: AedSellersComponent },
      { path: '!portal-accounts', component: AedPortalAccountsOffComponent },
    ],
  },
];

// Mounted under `!aed/!qr`, outside the portal layout: the address printed on the QR sticker,
// /aed/qr/{id_aed}, with `?t=<token>` in the link sent to the site manager.
export const AED_QR_ROUTES: Route[] = [
  {
    path: '',
    component: AedComponent,
    providers: [AedApiService],
    data: { app: true },
    children: [{ path: '!:id', component: AedQrComponent }],
  },
];
