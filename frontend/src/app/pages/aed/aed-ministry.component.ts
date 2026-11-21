import { Component, computed, effect, inject, OnInit, signal, untracked } from '@angular/core';
import { RouterLink } from '@angular/router';

import { SeoService } from '@app/services/seo.service';
import {
  AedApiService,
  AedDuplicate,
  aedErrorMessage,
  AedJobRun,
  aedLinkFactory,
  AedMapperRun,
  AedMessage,
  AedRemindersRun,
  AedStats,
  AedStatus,
} from './aed-api.service';
import { AedLoginComponent } from './aed-login.component';
import { AED_FIELDS, aedLabel } from './aed-schema';
import { AED_STATUS_LABELS, AedStatusComponent } from './aed-status.component';

const MESSAGE_KINDS: Record<string, string> = {
  aktywacja: 'Aktywacja urządzenia',
  prosba: 'Prośba o potwierdzenie danych',
  sygnal: 'Zgłoszenie osoby postronnej',
};

/** Ministry panel: numbers, duplicate review, the outbox of messages to device owners, cyclic jobs. */
@Component({
  selector: 'app-aed-ministry',
  standalone: true,
  imports: [RouterLink, AedLoginComponent, AedStatusComponent],
  templateUrl: './aed-ministry.component.html',
})
export class AedMinistryComponent implements OnInit {
  protected readonly api = inject(AedApiService);
  private readonly seo = inject(SeoService);

  protected readonly link = aedLinkFactory();
  protected readonly number = (value: number) => value.toLocaleString('pl-PL');
  protected readonly statusLabels = AED_STATUS_LABELS;
  protected readonly kind = (rodzaj: string) =>
    MESSAGE_KINDS[rodzaj] ?? (rodzaj.startsWith('termin_') ? 'Przypomnienie o terminie ważności' : rodzaj);

  protected readonly allowed = computed(() => this.api.account()?.rola === 'ministerstwo');
  protected readonly error = signal('');
  protected readonly busy = signal(false);

  protected readonly stats = signal<AedStats | null>(null);
  protected readonly statuses = computed(() => Object.entries(this.stats()?.wg_statusu ?? {}) as [AedStatus, number][]);
  protected readonly sources = computed(() =>
    Object.entries(this.stats()?.wg_zrodla ?? {}).sort(([, a], [, b]) => b - a),
  );

  protected readonly duplicates = signal<AedDuplicate[]>([]);
  protected readonly position = signal(0);
  protected readonly pair = computed(() => this.duplicates()[this.position()]);
  protected readonly decided = signal('');
  /** The two records of the current pair, field by field; fields empty in both are left out. */
  protected readonly comparison = computed(() => {
    const pair = this.pair();
    if (!pair) return [];
    return AED_FIELDS.map((field) => {
      const a = aedLabel(field, pair.rekord_a[field.name]);
      const b = aedLabel(field, pair.rekord_b[field.name]);
      return { title: field.title, a, b, same: a === b };
    }).filter((row) => row.a || row.b);
  });

  protected readonly messages = signal<AedMessage[]>([]);
  protected readonly messagesTotal = signal(0);
  protected readonly jobs = signal<AedJobRun[]>([]);
  protected readonly when = (iso: string | null | undefined) => (iso ? iso.slice(0, 16).replace('T', ', ') : '');
  protected readonly triggers = { harmonogram: 'Automatycznie, według harmonogramu', ministerstwo: 'Ręcznie z panelu' };
  protected readonly jobKinds = {
    cykl: 'Mapper i przypomnienia',
    mapper: 'Mapper źródeł',
    przypomnienia: 'Przypomnienia',
  };
  protected readonly reminders = signal<AedRemindersRun | null>(null);
  protected readonly mapper = signal<AedMapperRun | null>(null);

  private readonly fail = (error: unknown) => {
    this.error.set(aedErrorMessage(error as never));
    this.busy.set(false);
  };

  constructor() {
    // Load once the ministry account is signed in (also right after signing in on this page).
    effect(() => {
      if (this.allowed()) untracked(() => this.load());
    });
  }

  ngOnInit(): void {
    this.seo.setPageTitle(['Panel ministerstwa', 'Rejestr AED']);
  }

  private load(): void {
    this.api.stats().subscribe({ next: (stats) => this.stats.set(stats), error: this.fail });
    this.api.duplicates().subscribe({
      next: (page) => {
        this.duplicates.set(page.dane);
        this.position.set(Math.min(this.position(), Math.max(page.dane.length - 1, 0)));
      },
      error: this.fail,
    });
    this.api.jobs().subscribe({ next: (jobs) => this.jobs.set(jobs), error: this.fail });
    this.api.messages().subscribe({
      next: (page) => {
        this.messages.set(page.dane);
        this.messagesTotal.set(page.razem);
      },
      error: this.fail,
    });
  }

  protected skip(): void {
    if (this.busy()) return;
    this.decided.set('');
    this.position.set((this.position() + 1) % this.duplicates().length);
  }

  protected decide(decyzja: 'polacz' | 'rozdziel'): void {
    const pair = this.pair();
    if (this.busy()) return;
    this.busy.set(true);
    this.api.decideDuplicate(pair.id, decyzja).subscribe({
      next: () => {
        this.decided.set(
          decyzja === 'polacz'
            ? `Połączono: został rekord ${pair.rekord_a.id_aed}, rekord ${pair.rekord_b.id_aed} jest wycofany.`
            : `Zostają oba rekordy: ${pair.rekord_a.id_aed} i ${pair.rekord_b.id_aed}.`,
        );
        this.error.set('');
        this.busy.set(false);
        this.load();
      },
      error: this.fail,
    });
  }

  protected runReminders(): void {
    if (this.busy()) return;
    this.busy.set(true);
    this.api.runReminders().subscribe({
      next: (result) => {
        this.reminders.set(result);
        this.busy.set(false);
        this.load();
      },
      error: this.fail,
    });
  }

  protected runMapper(): void {
    if (this.busy()) return;
    this.busy.set(true);
    this.api.runMapper().subscribe({
      next: (result) => {
        this.mapper.set(result);
        this.busy.set(false);
        this.load();
      },
      error: this.fail,
    });
  }
}
