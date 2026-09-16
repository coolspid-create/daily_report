const { test } = require('node:test');
const assert = require('node:assert/strict');
const { decide } = require('./press-watchdog.cjs');

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
