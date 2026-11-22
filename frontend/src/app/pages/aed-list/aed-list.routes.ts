import { Routes } from '@angular/router';

import { DgaInformationPointTablePageComponent } from '@app/pages/dga-information-point/dga-information-point-table-page/dga-information-point-table-page.component';
import { DgaInformationPointTableComponent } from '@app/pages/dga-information-point/dga-information-point-table/dga-information-point-table.component';
import { breadcrumbsAedListTableDataResolverService } from '@app/shared/breadcrumbs/resolvers/breadcrumbs-aed-list-table-data-resolver.service';

/**
 * National AED list: the same page as the DGA "list of protected data" (resource header, downloads, table, CMS text),
 * fed by /aed-aggregated instead of /dga-aggregated. The DGA components are generic, so they are reused as they are.
 */
export const AED_LIST_ROUTES: Routes = [
  {
    path: '',
    component: DgaInformationPointTablePageComponent,
    children: [
      { path: '', redirectTo: '!table', pathMatch: 'full' },
      { path: '!table', component: DgaInformationPointTableComponent },
    ],
    data: { breadcrumbs: { dataKey: 'post.cms.title' } },
    resolve: { post: breadcrumbsAedListTableDataResolverService },
  },
];
