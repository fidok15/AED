import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import { lastValueFrom, Observable, of, throwError, toArray } from 'rxjs';

import { AedListService } from '@app/services/aed-list.service';
import { CmsService } from '@app/services/cms.service';
import { DatasetService } from '@app/services/dataset.service';
import { breadcrumbsAedListTableDataResolverService } from '@app/shared/breadcrumbs/resolvers/breadcrumbs-aed-list-table-data-resolver.service';

describe('breadcrumbsAedListTableDataResolverService', () => {
  const aggregated = {
    updated_at: '2026-11-22T03:45:00Z',
    resource_id: 781,
    resource_slug: 'krajowy-wykaz-aed',
    dataset_id: 12,
    dataset_slug: 'krajowy-wykaz',
  };
  const resource = { id: '781', attributes: { title: 'Krajowy wykaz AED', files: [] } };
  const stats = { data: { attributes: { views_count: 3, downloads_count: 1 } } };
  const cms = { title: 'Wykaz AED', body: [] };

  let aedListService: { getAedAggregatedData: jest.Mock };
  let datasetService: { getResourceById: jest.Mock; getDatasetsStats: jest.Mock };
  let cmsService: { getLandingPage: jest.Mock };
  let router: { navigate: jest.Mock };
  let translate: { instant: jest.Mock };

  const route = { queryParams: {} } as unknown as ActivatedRouteSnapshot;
  const state = { url: '/pl/wykaz-aed/table' } as RouterStateSnapshot;

  const resolve = (): Promise<unknown[]> =>
    lastValueFrom(
      (
        TestBed.runInInjectionContext(() =>
          breadcrumbsAedListTableDataResolverService(route, state),
        ) as Observable<unknown>
      ).pipe(toArray()),
    );

  beforeEach(() => {
    aedListService = { getAedAggregatedData: jest.fn(() => of(aggregated)) };
    datasetService = { getResourceById: jest.fn(() => of(resource)), getDatasetsStats: jest.fn(() => of(stats)) };
    cmsService = { getLandingPage: jest.fn(() => of(cms)) };
    router = { navigate: jest.fn(() => Promise.resolve(true)) };
    translate = { instant: jest.fn((key: string) => (key === 'Menu.AedList' ? 'Wykaz AED' : key)) };
    jest.spyOn(console, 'warn').mockImplementation(() => undefined);

    TestBed.configureTestingModule({
      providers: [
        { provide: AedListService, useValue: aedListService },
        { provide: DatasetService, useValue: datasetService },
        { provide: CmsService, useValue: cmsService },
        { provide: Router, useValue: router },
        { provide: TranslateService, useValue: translate },
      ],
    });
  });

  it('builds post data from /aed-aggregated, the resource, dataset stats and the CMS page', async () => {
    const emitted = await resolve();

    expect(datasetService.getResourceById).toHaveBeenCalledWith('781');
    expect(datasetService.getDatasetsStats).toHaveBeenCalledWith('12', 'krajowy-wykaz');
    expect(cmsService.getLandingPage).toHaveBeenCalledWith('/wykaz-aed', undefined, undefined);
    expect(emitted).toEqual([{ resData: aggregated, resource, stats, cms }]);
    expect(router.navigate).not.toHaveBeenCalled();
  });

  it('navigates home and emits nothing when /aed-aggregated fails (no national list yet)', async () => {
    aedListService.getAedAggregatedData.mockReturnValue(throwError(() => ({ status: 404 })));

    expect(await resolve()).toEqual([]);
    expect(router.navigate).toHaveBeenCalledWith(['/']);
    expect(datasetService.getResourceById).not.toHaveBeenCalled();
  });

  it('still shows the national list when the CMS page is missing, titled from translations and without CMS text', async () => {
    cmsService.getLandingPage.mockReturnValue(throwError(() => ({ status: 404 })));

    const emitted = await resolve();

    expect(emitted).toEqual([{ resData: aggregated, resource, stats, cms: { title: 'Wykaz AED', body: [] } }]);
    expect(translate.instant).toHaveBeenCalledWith('Menu.AedList');
    expect(router.navigate).not.toHaveBeenCalled();
  });

  it('navigates home when the national list resource cannot be loaded', async () => {
    datasetService.getResourceById.mockReturnValue(throwError(() => ({ status: 404 })));

    expect(await resolve()).toEqual([]);
    expect(router.navigate).toHaveBeenCalledWith(['/']);
  });

  it('asks /aed-aggregated on every resolve, so a new merge is picked up', async () => {
    await resolve();
    aedListService.getAedAggregatedData.mockReturnValue(of({ ...aggregated, resource_id: 782 }));
    await resolve();

    expect(aedListService.getAedAggregatedData).toHaveBeenCalledTimes(2);
    expect(datasetService.getResourceById).toHaveBeenLastCalledWith('782');
  });
});
