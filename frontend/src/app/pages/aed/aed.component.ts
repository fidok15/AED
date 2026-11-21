import { Component, inject, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { LocalizeRouterPipe } from '@gilsdav/ngx-translate-router';

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
}
