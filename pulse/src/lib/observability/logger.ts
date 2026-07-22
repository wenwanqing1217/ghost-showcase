export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: string;
  service: string;
  meta?: Record<string, unknown>;
}

const SERVICE = 'ds';

export function log(level: LogLevel, message: string, meta?: Record<string, unknown>) {
  const entry: LogEntry = {
    level,
    message,
    timestamp: new Date().toISOString(),
    service: SERVICE,
    meta,
  };

  // In production, replace with your observability provider:
  // - Vercel: `console.log(JSON.stringify(entry))` → captured by Vercel logs
  // - Datadog / Axiom / Better Stack: send via their SDK
  // - Local dev: pretty-print to console

  const serialized = JSON.stringify(entry);

  switch (level) {
    case 'debug':
      console.debug(serialized);
      break;
    case 'info':
      console.info(serialized);
      break;
    case 'warn':
      console.warn(serialized);
      break;
    case 'error':
      console.error(serialized);
      break;
  }
}

export const logger = {
  debug: (message: string, meta?: Record<string, unknown>) => log('debug', message, meta),
  info: (message: string, meta?: Record<string, unknown>) => log('info', message, meta),
  warn: (message: string, meta?: Record<string, unknown>) => log('warn', message, meta),
  error: (message: string, meta?: Record<string, unknown>) => log('error', message, meta),
};
