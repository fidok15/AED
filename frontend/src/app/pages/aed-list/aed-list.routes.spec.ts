import { AED_LIST_ROUTES } from '@app/pages/aed-list/aed-list.routes';
import { DgaInformationPointTablePageComponent } from '@app/pages/dga-information-point/dga-information-point-table-page/dga-information-point-table-page.component';
import { DgaInformationPointTableComponent } from '@app/pages/dga-information-point/dga-information-point-table/dga-information-point-table.component';
import { breadcrumbsAedListTableDataResolverService } from '@app/shared/breadcrumbs/resolvers/breadcrumbs-aed-list-table-data-resolver.service';

describe('AED_LIST_ROUTES', () => {
  it('shows the national AED list with the same page and table components as the DGA list', () => {
    const [page] = AED_LIST_ROUTES;

    expect(AED_LIST_ROUTES).toHaveLength(1);
    expect(page.component).toBe(DgaInformationPointTablePageComponent);
    expect(page.resolve).toEqual({ post: breadcrumbsAedListTableDataResolverService });
    expect(page.data).toEqual({ breadcrumbs: { dataKey: 'post.cms.title' } });
    expect(page.children).toEqual([
      { path: '', redirectTo: '!table', pathMatch: 'full' },
      { path: '!table', component: DgaInformationPointTableComponent },
    ]);
  });
});
