const { test } = require('node:test');
const assert = require('node:assert/strict');
const { decide, shouldCollect } = require('./press-watchdog.cjs');

const afternoon = new Date('2026-09-09T16:34:00+09:00');
const morningRun = {
  head_branch: 'main', display_title: 'Collector / press',
  created_at: '2026-09-09T01:30:25Z', status: 'completed', conclusion: 'success',
};

test('delayed watchdog recognizes the successful morning collection', () => {
  assert.equal(decide([morningRun], afternoon).fallback, false);
});
test('queued collection suppresses fallback', () => {
  assert.equal(decide([{ ...morningRun, status: 'queued', conclusion: null }], afternoon).fallback, false);
});
test('reports and yesterday do not mask missing press collection', () => {
  assert.deepEqual(decide([
    { ...morningRun, display_title: 'Collector / scheduled' },
    { ...morningRun, created_at: '2026-09-08T01:30:25Z' },
  ], afternoon), { fallback: true, reason: 'missing' });
});
test('failed press collection allows fallback', () => {
  assert.deepEqual(decide([{ ...morningRun, conclusion: 'failure' }], afternoon),
    { fallback: true, reason: 'failed' });
});
test('weekend and before check time never trigger fallback', () => {
  for (const date of ['2026-09-06T16:30:00+09:00', '2026-09-09T10:45:00+09:00']) {
    assert.equal(decide([], new Date(date)).fallback, false);
  }
});
test('Friday remains eligible', () => {
  assert.equal(decide([], new Date('2026-09-11T11:45:00+09:00')).fallback, true);
});
test('failed backup is not repeated on the same day', () => {
  assert.equal(decide([
    { ...morningRun, conclusion: 'failure' },
    { ...morningRun, display_title: 'Collector / press-fallback', conclusion: 'failure' },
  ], afternoon).fallback, false);
});
test('legacy records do not cause rollout false alarms', () => {
  assert.equal(decide([{ ...morningRun, display_title: 'Collector' }], afternoon).fallback, false);
});

test('report backup runs at 09:25 KST only when the report run is missing or failed', () => {
  const checkAt = new Date('2026-09-09T09:25:00+09:00');
  const report = { ...morningRun, created_at: '2026-09-08T23:35:04Z', display_title: 'Collector / scheduled' };
  assert.equal(decide([], new Date('2026-09-09T09:24:59+09:00'), 'scheduled').fallback, false);
  assert.deepEqual(decide([], checkAt, 'scheduled'), { fallback: true, reason: 'missing' });
  assert.equal(decide([report], checkAt, 'scheduled').fallback, false);
  assert.deepEqual(decide([{ ...report, conclusion: 'failure' }], checkAt, 'scheduled'),
    { fallback: true, reason: 'failed' });
});

test('serialized automatic collectors skip a previous success and ignore other queued jobs', () => {
  assert.equal(shouldCollect([morningRun], afternoon, 'press', false, 42), false);
  assert.equal(shouldCollect([{ ...morningRun, status: 'queued' }], afternoon, 'press', false, 42), true);
  assert.equal(shouldCollect([{ ...morningRun, id: 42 }], afternoon, 'press', false, 42), true);
  const failedBackup = { ...morningRun, conclusion: 'failure', display_title: 'Collector / press-fallback' };
  assert.equal(shouldCollect([failedBackup], afternoon, 'press', true, 42), false);
  assert.equal(shouldCollect([failedBackup], afternoon, 'press', false, 42), true);
});
