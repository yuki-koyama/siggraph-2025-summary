const TAG_ORDER = [
  'conference',
  'journal',
  'invited-tog',
  'conference-deferred',
  'journal-deferred',
];

const TAG_LABELS = {
  conference: 'Conference Papers',
  journal: 'Journal Papers',
  'invited-tog': 'Invited from TOG',
  'conference-deferred': 'Conference Papers (Deferred Paper Presentation)',
  'journal-deferred': 'Journal Papers (Deferred Paper Presentation)',
};

function preparePaperData(data) {
  const presentedPapers = data.filter(paper => !paper.is_deferred);
  const deferredPapers = data.filter(paper => paper.is_deferred);
  const sessionsMap = new Map();

  for (const paper of presentedPapers) {
    const name = paper.session || 'Unknown Session';
    if (!sessionsMap.has(name)) {
      sessionsMap.set(name, []);
    }
    sessionsMap.get(name).push(paper);
  }

  const sessions = Array.from(
    sessionsMap,
    ([name, papers]) => ({ name, papers })
  );
  const tagCounts = TAG_ORDER.map(tag => ({
    tag,
    label: TAG_LABELS[tag],
    count: data.filter(paper => paper.paper_type === tag).length,
  })).filter(item => item.count > 0);

  return {
    sessions,
    deferredPapers,
    tagCounts,
    sessionCount: sessions.length,
    presentedPaperCount: presentedPapers.length,
    deferredPaperCount: deferredPapers.length,
    totalPaperCount: data.length,
  };
}

module.exports = { preparePaperData };
