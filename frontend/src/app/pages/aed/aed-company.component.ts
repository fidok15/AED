import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LocalizeRouterPipe } from '@gilsdav/ngx-translate-router';

import { SeoService } from '@app/services/seo.service';
import { AedApiService, aedErrorMessage, aedLinkFactory, AedSellers, AedSubmission } from './aed-api.service';
import { AedLoginComponent } from './aed-login.component';
import { AED_FIELDS, aedField, aedRequired, aedScoreFields } from './aed-schema';

/** Company panel: sign in, check a CSV file, send it, get the QR links for the accepted devices. */
@Component({
  selector: 'app-aed-company',
  standalone: true,
  imports: [RouterLink, LocalizeRouterPipe, AedLoginComponent],
  templateUrl: './aed-company.component.html',
})
export class AedCompanyComponent implements OnInit {
  protected readonly api = inject(AedApiService);
  private readonly seo = inject(SeoService);

  protected readonly required = aedRequired('sprzedaz').map(aedField);
  /** Header row of the standard, built from the schema, offered as a starting file. */
  protected readonly templateHref =
    'data:text/csv;charset=utf-8,' + encodeURIComponent(AED_FIELDS.map((field) => field.name).join(',') + '\n');
  protected readonly title = (column: string) => aedField(column)?.title ?? column;

  protected readonly qrLink = aedLinkFactory();

  // Score of the signed-in company, from the public ranking, and what raises it (weights from the schema).
  private readonly sellers = signal<AedSellers | null>(null);
  protected readonly score = computed(() =>
    this.sellers()?.dane.find((seller) => seller.nazwa === this.api.account()?.nazwa),
  );
  protected readonly thresholds = computed(() => this.sellers()?.progi);
  protected readonly sellerScore = aedScoreFields('sprzedawca');
  protected readonly managerScore = aedScoreFields('dysponent').filter((field) => field.waga >= 2);
  protected readonly number = (value: number) => value.toLocaleString('pl-PL');
  protected readonly points = (waga: number) => (waga === 1 ? '1 punkt' : `${waga} punkty`);

  protected readonly file = signal<File | null>(null);
  protected readonly report = signal<AedSubmission | null>(null);
  protected readonly saved = signal(false);
  protected readonly busy = signal(false);
  protected readonly error = signal('');

  ngOnInit(): void {
    this.seo.setPageTitle(['Panel firmy', 'Rejestr AED']);
    this.loadScore();
  }

  private loadScore(): void {
    this.api.sellers().subscribe({ next: (sellers) => this.sellers.set(sellers), error: () => this.sellers.set(null) });
  }

  protected choose(input: HTMLInputElement): void {
    this.file.set(input.files?.[0] ?? null);
    this.report.set(null);
    this.saved.set(false);
    if (this.file()) this.send(false);
  }

  /** `save = false` asks only for the report; `save = true` adds the correct rows to the registry. */
  protected send(save: boolean): void {
    this.busy.set(true);
    this.api.submitCsv(this.file(), save).subscribe({
      next: (report) => {
        this.report.set(report);
        this.saved.set(save);
        if (save) this.loadScore();
        this.error.set('');
        this.busy.set(false);
      },
      error: (error) => {
        this.error.set(aedErrorMessage(error));
        this.busy.set(false);
      },
    });
  }
}
