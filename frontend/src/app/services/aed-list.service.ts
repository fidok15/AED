import { DOCUMENT } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Inject, Injectable, PLATFORM_ID } from '@angular/core';
import { Router } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import { CookieService } from 'ngx-cookie-service';
import { LocalStorageService } from 'ngx-localstorage';
import { Observable } from 'rxjs';

import { ApiConfig } from '@app/services/api';
import { LoginService } from '@app/services/login-service';
import { NotificationsService } from '@app/services/notifications.service';
import { RestService } from '@app/services/rest.service';

/** Where the national AED list lives in the portal (`GET /aed-aggregated`, backend `mcod/aed/views.py`). */
export interface IAedAggregated {
  dataset_id: number;
  dataset_slug: string;
  resource_id: number;
  resource_slug: string;
  updated_at: string;
  report?: Record<string, unknown>;
}

@Injectable({
  providedIn: 'root',
})
export class AedListService extends RestService {
  readonly ApiConfig = ApiConfig;

  constructor(
    protected http: HttpClient,
    public translate: TranslateService,
    public router: Router,
    public notificationService: NotificationsService,
    public storageService: LocalStorageService,
    public cookieService: CookieService,
    public loginService: LoginService,
    @Inject(DOCUMENT) public document: Document,
    @Inject(PLATFORM_ID) public platformId: string,
  ) {
    super(
      http,
      translate,
      router,
      notificationService,
      storageService,
      cookieService,
      loginService,
      document,
      platformId,
    );
  }

  getAedAggregatedData(): Observable<IAedAggregated> {
    return this.get(this.ApiConfig.aed_aggregated);
  }
}
