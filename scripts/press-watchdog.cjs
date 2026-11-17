const MODES = {
  scheduled: { start: '08:35', checkAt: '09:25', title: 'Collector / scheduled', fallback: 'Collector / report-fallback' },
  press: { start: '10:30', checkAt: '11:45', title: 'Collector / press', fallback: 'Collector / press-fallback' },
};

function collectionWindow(now, mode, checkBackup) {
  const schedule = MODES[mode];
  const kst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  const day = kst.toISOString().slice(0, 10);
  return {
    start: new Date(`${day}T${schedule.start}:00+09:00`),
    eligible: kst.getUTCDay() >= 1 && kst.getUTCDay() <= 5
      && now >= new Date(`${day}T${checkBackup ? schedule.checkAt : schedule.start}:00+09:00`),
  };
}

function todayRuns(runs, now, start) {
  return runs.filter((run) => run.head_branch === 'main'
    && new Date(run.created_at) >= start && new Date(run.created_at) <= now);
}

function decide(runs, now, mode = 'press') {
  const { start, eligible } = collectionWindow(now, mode, true);
  if (!eligible) return { fallback: false, reason: 'outside-window' };
  const schedule = MODES[mode];
  const today = todayRuns(runs, now, start);
  if (today.some((run) => run.display_title === schedule.fallback && run.conclusion !== 'cancelled')) {
    return { fallback: false, reason: 'fallback-already-attempted' };
  }
  // Older runs have no mode in their title. Do not infer a missing collection
  // from ambiguous historical records during rollout of the new run names.
  if (today.some((run) => run.display_title === 'Collector')) {
    return { fallback: false, reason: 'legacy-run-unclassified' };
  }
  const primary = today.filter((run) => run.display_title === schedule.title);
  if (primary.some((run) => run.status !== 'completed' || run.conclusion === 'success')) {
    return { fallback: false, reason: 'already-started-or-succeeded' };
  }
  return { fallback: true, reason: primary.length ? 'failed' : 'missing' };
}

function shouldCollect(runs, now, mode, isFallback, runId) {
  const { start, eligible } = collectionWindow(now, mode, false);
  if (!eligible) return false;
  const schedule = MODES[mode];
  // Collection jobs are serialized. Ignore queued runs and this run itself.
  return !todayRuns(runs, now, start).some((run) =>
    run.id !== runId && run.status === 'completed'
    && (([schedule.title, schedule.fallback].includes(run.display_title) && run.conclusion === 'success')
      || (isFallback && run.display_title === schedule.fallback && run.conclusion === 'failure')));
}

async function listRuns(github, context, start) {
  return github.paginate(github.rest.actions.listWorkflowRuns, {
    owner: context.repo.owner,
    repo: context.repo.repo,
    workflow_id: 'collector.yml',
    branch: 'main',
    created: `>=${start.toISOString()}`,
    per_page: 100,
  });
}

async function check({ github, context, core, mode }) {
  const now = new Date();
  const { start, eligible } = collectionWindow(now, mode, true);
  const runs = eligible ? await listRuns(github, context, start) : [];
  const result = decide(runs, now, mode);
  core.setOutput('fallback_required', String(result.fallback));
  core.setOutput('reason', result.reason);
  core.info(JSON.stringify({ mode, checkedAt: now.toISOString(), start, ...result }));
}

async function checkCollector({ github, context, core, mode, isFallback }) {
  const now = new Date();
  const { start, eligible } = collectionWindow(now, mode, false);
  const runs = eligible ? await listRuns(github, context, start) : [];
  core.setOutput('collect', String(shouldCollect(runs, now, mode, isFallback, context.runId)));
}

module.exports = { check, decide, checkCollector, shouldCollect };
