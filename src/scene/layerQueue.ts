/**
 * Loads layers one after another. A layer that fails stays failed until retry(),
 * so an overlapping call never reloads it behind the user's back while the
 * "Coba lagi" banner is still showing. reset() starts a new generation: earlier
 * loads are told they are stale and earlier queues stop.
 */
export class LayerQueue<K> {
  private generation = 0;
  private readonly loaded = new Set<K>();
  private readonly failed = new Set<K>();
  private readonly pending = new Map<K, Promise<void>>();

  constructor(
    private readonly load: (key: K, isCurrent: () => boolean) => Promise<void>,
    private readonly onError: (key: K, error: unknown) => void,
  ) {}

  async ensure(keys: readonly K[]): Promise<void> {
    const generation = this.generation;
    for (const key of keys) {
      if (generation !== this.generation) return;
      if (this.loaded.has(key) || this.failed.has(key)) continue;
      await this.start(key);
    }
  }

  retry(key: K): void {
    this.failed.delete(key);
  }

  reset(): void {
    this.generation += 1;
    this.loaded.clear();
    this.failed.clear();
    this.pending.clear();
  }

  private start(key: K): Promise<void> {
    const existing = this.pending.get(key);
    if (existing) return existing;
    const generation = this.generation;
    const isCurrent = () => generation === this.generation;
    const promise = this.load(key, isCurrent)
      .then(
        () => {
          if (isCurrent()) this.loaded.add(key);
        },
        (error: unknown) => {
          if (!isCurrent()) return;
          this.failed.add(key);
          this.onError(key, error);
        },
      )
      .finally(() => {
        if (isCurrent()) this.pending.delete(key);
      });
    this.pending.set(key, promise);
    return promise;
  }
}
