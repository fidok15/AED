import { inject } from '@angular/core';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import { combineLatest, EMPTY, Observable, of } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';

import { CmsService } from '@app/services/cms.service';
import { DatasetService } from '@app/services/dataset.service';
import { AedListService, IAedAggregated } from '@app/services/aed-list.service';

export const breadcrumbsAedListTableDataResolverService = (
  route: ActivatedRouteSnapshot,
  state: RouterStateSnapshot,
) => {
  const aedListService = inject(AedListService);
  const datasetService = inject(DatasetService);
  const cmsService = inject(CmsService);
  const router = inject(Router);
  const translate = inject(TranslateService);

  const getMoreData = (data: IAedAggregated): Observable<unknown> => {
    const lang = route.queryParams.lang;
    const url = state.url.substring(3);
    const slicedUrl = url.slice(0, url.lastIndexOf('/'));
    const rev = route.queryParams.rev;

    return combineLatest([
      of(data),
      datasetService.getResourceById(String(data.resource_id)),
      datasetService.getDatasetsStats(String(data.dataset_id), data.dataset_slug),
      // Unlike DGA, the list stays visible without its CMS page (not created yet in a given portal):
      // the page then has only a title and no descriptive text.
      cmsService
        .getLandingPage(slicedUrl, lang, rev)
        .pipe(catchError(() => of({ title: translate.instant('Menu.AedList'), body: [] }))),
    ]).pipe(
      map(([resData, resource, stats, cms]) => {
        return {
          resData,
          resource,
          stats,
          cms,
        };
      }),
    );
  };

  return aedListService.getAedAggregatedData().pipe(
    switchMap((responseData) => getMoreData(responseData)),
    catchError(() => {
      console.warn("Couldn't load data");
      router.navigate(['/']).then();
      return EMPTY;
    }),
  );
};
