import { LayerQueue } from './layerQueue';

function deferred() {
  let resolve!: () => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<void>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

test('one failing layer reports an error and the others still load', async () => {
  const onError = vi.fn();
  const loaded: string[] = [];
  const queue = new LayerQueue<string>(async (key) => {
    if (key === 'b') throw new Error('404');
    loaded.push(key);
  }, onError);
  await queue.ensure(['a', 'b', 'c']);
  expect(loaded).toEqual(['a', 'c']);
  expect(onError).toHaveBeenCalledWith('b', expect.any(Error));
});

test('a failed layer is not loaded again until retry', async () => {
  const load = vi.fn(async () => {
    throw new Error('offline');
  });
  const queue = new LayerQueue<string>(load, () => {});
  await queue.ensure(['b']);
  await queue.ensure(['b']);
  expect(load).toHaveBeenCalledTimes(1);
  queue.retry('b');
  await queue.ensure(['b']);
  expect(load).toHaveBeenCalledTimes(2);
});

test('an overlapping call does not reload a layer that failed in the other call', async () => {
  const gates = { skin: deferred(), digestive: deferred(), muscle: deferred() };
  const load = vi.fn((key: keyof typeof gates) => gates[key].promise);
  const queue = new LayerQueue(load, () => {});
  const first = queue.ensure(['skin', 'digestive']);
  const second = queue.ensure(['muscle', 'digestive']);
  gates.skin.resolve();
  await Promise.resolve();
  gates.digestive.reject(new Error('404'));
  await first;
  gates.muscle.resolve();
  await second;
  expect(load.mock.calls.filter(([key]) => key === 'digestive')).toHaveLength(1);
});

test('reset forgets earlier results and stops the earlier queue', async () => {
  const gate = deferred();
  const load = vi.fn((key: string) => (key === 'a' ? gate.promise : Promise.resolve()));
  const queue = new LayerQueue<string>(load, () => {});
  const before = queue.ensure(['a', 'b']);
  queue.reset();
  gate.resolve();
  await before;
  expect(load).not.toHaveBeenCalledWith('b', expect.anything());
  await queue.ensure(['a']);
  expect(load.mock.calls.filter(([key]) => key === 'a')).toHaveLength(2);
});

test('the load is told when its result has gone stale', async () => {
  const gate = deferred();
  let isCurrent: (() => boolean) | undefined;
  const queue = new LayerQueue<string>((_key, current) => {
    isCurrent = current;
    return gate.promise;
  }, () => {});
  const pending = queue.ensure(['a']);
  expect(isCurrent?.()).toBe(true);
  queue.reset();
  expect(isCurrent?.()).toBe(false);
  gate.resolve();
  await pending;
});
