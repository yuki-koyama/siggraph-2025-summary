const EVENTS = {
  'siggraph-2025': {
    pageTitle: 'SIGGRAPH 2025 Technical Papers',
    sourceUrl: 'https://s2025.conference-schedule.org/',
    sourceLabel: 's2025.conference-schedule.org',
  },
  'siggraph-asia-2025': {
    pageTitle: 'SIGGRAPH Asia 2025 Technical Papers',
    sourceUrl: 'https://sa2025.conference-schedule.org/',
    sourceLabel: 'sa2025.conference-schedule.org',
  },
};

const DEFAULT_EVENT = 'siggraph-2025';

function getEventFromArgv(argv) {
  const eventFlagIndex = argv.indexOf('--event');
  const event = eventFlagIndex >= 0 ? argv[eventFlagIndex + 1] : DEFAULT_EVENT;
  if (!EVENTS[event]) {
    const keys = Object.keys(EVENTS).join(', ');
    throw new Error(`Unsupported event "${event}". Available events: ${keys}`);
  }
  return event;
}

module.exports = {
  EVENTS,
  DEFAULT_EVENT,
  getEventFromArgv,
};
