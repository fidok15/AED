import { Component, inject, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { LocalizeRouterPipe, LocalizeRouterService } from '@gilsdav/ngx-translate-router';

/**
 * Shell of the AED area. It owns the only AED stylesheet (every rule is scoped under `.aed`).
 * Route data `app: true` switches to the phone screen opened from a QR sticker: no portal header,
 * so the site manager lands straight on the task.
 */
@Component({
  selector: 'app-aed',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, LocalizeRouterPipe],
  templateUrl: './aed.component.html',
  styleUrl: './aed.scss',
  encapsulation: ViewEncapsulation.None,
})
export class AedComponent {
  protected readonly app: boolean = inject(ActivatedRoute).snapshot.data['app'] === true;
  private readonly router = inject(Router);
  private readonly localize = inject(LocalizeRouterService);

  protected readonly links = [
    { path: ['/!aed'], label: 'Start', exact: true },
    { path: ['/!aed', '!registry'], label: 'Rejestr urządzeń', exact: false },
    { path: ['/!aed', '!company'], label: 'Panel firmy', exact: false },
    { path: ['/!aed', '!ministry'], label: 'Panel ministerstwa', exact: false },
    { path: ['/!aed', '!sellers'], label: 'Ranking firm', exact: false },
    { path: ['/!aed', '!konwerter'], label: 'Konwerter', exact: false },
  ];

  /** Label of the section on screen, for the narrow-screen menu (re-read on every change detection). */
  protected current(): string {
    const active = this.links.find(({ path, exact }) =>
      this.router.isActive(this.router.createUrlTree(this.localize.translateRoute(path) as string[]), {
        paths: exact ? 'exact' : 'subset',
        queryParams: 'ignored',
        fragment: 'ignored',
        matrixParams: 'ignored',
      }),
    );
    return active?.label ?? 'Opiekun AED';
  }
}
