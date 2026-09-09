function collectionWindow(now) {
  const kst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  const day = kst.toISOString().slice(0, 10);
  return {
    start: new Date(`${day}T10:30:00+09:00`),
    eligible: kst.getUTCDay() >= 1 && kst.getUTCDay() <= 5
      && now >= new Date(`${day}T11:45:00+09:00`),
  };
}

function decide(runs, now) {
  const { start, eligible } = collectionWindow(now);
  if (!eligible) return { fallback: false, reason: 'outside-window' };
  const today = runs.filter((run) => run.head_branch === 'main'
    && new Date(run.created_at) >= start && new Date(run.created_at) <= now);
  // Older runs have no mode in their title. Do not infer a missing collection
  // from ambiguous historical records during rollout of the new run names.
  if (today.some((run) => run.display_title === 'Collector')) {
    return { fallback: false, reason: 'legacy-run-unclassified' };
  }
  const press = today.filter((run) => run.display_title === 'Collector / press');
  if (press.some((run) => run.status !== 'completed' || run.conclusion === 'success')) {
    return { fallback: false, reason: 'already-started-or-succeeded' };
  }
  return { fallback: true, reason: press.length ? 'failed' : 'missing' };
}

async function check({ github, context, core }) {
  const now = new Date();
  const { start, eligible } = collectionWindow(now);
  let runs = [];
  if (eligible) {
    runs = await github.paginate(github.rest.actions.listWorkflowRuns, {
      owner: context.repo.owner,
      repo: context.repo.repo,
      workflow_id: 'collector.yml',
      event: 'workflow_dispatch',
      branch: 'main',
      created: `>=${start.toISOString()}`,
      per_page: 100,
    });
  }
  const result = decide(runs, now);
  core.setOutput('fallback_required', String(result.fallback));
  core.setOutput('reason', result.reason);
  core.info(JSON.stringify({ checkedAt: now.toISOString(), start, ...result }));
}

module.exports = { check, decide };
