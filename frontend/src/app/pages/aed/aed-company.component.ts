import { Component, computed, effect, inject, OnInit, signal, untracked } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LocalizeRouterPipe } from '@gilsdav/ngx-translate-router';

import { SeoService } from '@app/services/seo.service';
import {
  AedAccepted,
  AedApiService,
  aedErrorMessage,
  aedFileTooLarge,
  aedFocusFactory,
  aedLinkFactory,
  AedSellers,
  AedSubmission,
} from './aed-api.service';
import { AedLoginComponent } from './aed-login.component';
import { AED_FIELDS, aedField, aedRequired, aedScoreFields } from './aed-schema';

// Fictional values for the example files; other columns take the example from the schema.
const EXAMPLE: Record<string, string> = {
  producent: 'FikcjaMed',
  model: 'DemoAED 200',
  dysponent_nazwa: 'Szkoła Podstawowa nr 0 w Fikcyjnowie (DEMO)',
  dysponent_email: 'sekretariat-sp0@demo.example',
};

/** Three example devices in the columns of profile `sprzedaz`, with new serial numbers on every call. */
function exampleCsv(withErrors: boolean): string {
  const columns = aedRequired('sprzedaz');
  const stamp = Date.now().toString(36).toUpperCase();
  const rows = [1, 2, 3].map((n) =>
    Object.fromEntries(
      columns.map((column) => [
        column,
        column === 'numer_seryjny' ? `DEMO-${stamp}-${n}` : (EXAMPLE[column] ?? aedField(column).przyklad ?? ''),
      ]),
    ),
  );
  if (withErrors) {
    rows[0]['numer_seryjny'] = '';
    rows[1]['data_produkcji'] = '15.03.2024';
    rows[2]['dysponent_email'] = 'sekretariat(at)szkola';
  }
  const lines = [columns.join(','), ...rows.map((row) => columns.map((column) => row[column]).join(','))];
  return 'data:text/csv;charset=utf-8,' + encodeURIComponent(lines.join('\r\n') + '\r\n');
}

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
  /** Example files for the demo, rebuilt after every submission so their serial numbers stay new. */
  protected readonly exampleHref = signal(exampleCsv(false));
  protected readonly exampleErrorsHref = signal(exampleCsv(true));

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

  /** Devices accepted in earlier submissions: their stickers and manager links stay available here. */
  protected readonly reported = signal<AedAccepted[]>([]);
  private readonly focus = aedFocusFactory();

  protected readonly file = signal<File | null>(null);
  protected readonly report = signal<AedSubmission | null>(null);
  protected readonly saved = signal(false);
  protected readonly busy = signal(false);
  protected readonly error = signal('');

  constructor() {
    // Load the score and earlier submissions when a company account is signed in (also after signing in here).
    effect(() => {
      if (this.api.account()) untracked(() => this.loadScore());
    });
  }

  ngOnInit(): void {
    this.seo.setPageTitle(['Panel firmy', 'Rejestr AED']);
  }

  private loadScore(): void {
    this.api.sellers().subscribe({ next: (sellers) => this.sellers.set(sellers), error: () => this.sellers.set(null) });
    if (this.api.account()?.rola !== 'firma') return;
    this.api.submissions().subscribe({
      next: (submissions) => this.reported.set(submissions.flatMap((submission) => submission.przyjete)),
      error: () => this.reported.set([]),
    });
  }

  protected choose(input: HTMLInputElement): void {
    this.file.set(input.files?.[0] ?? null);
    this.report.set(null);
    this.saved.set(false);
    this.error.set(aedFileTooLarge(this.file()));
    if (this.file() && !this.error()) this.send(false);
  }

  /** `save = false` asks only for the report; `save = true` adds the correct rows to the registry. */
  protected send(save: boolean): void {
    if (this.busy()) return;
    this.busy.set(true);
    this.api.submitCsv(this.file(), save).subscribe({
      next: (report) => {
        this.report.set(report);
        this.saved.set(save);
        if (save) {
          this.focus('#aed-report-heading');
          this.loadScore();
          this.exampleHref.set(exampleCsv(false));
          this.exampleErrorsHref.set(exampleCsv(true));
        }
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
