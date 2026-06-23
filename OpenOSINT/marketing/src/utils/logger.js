function timestamp() {
  return new Date().toISOString();
}

function format(level, context, message, data) {
  const base = `[${timestamp()}] [${level}] [${context}] ${message}`;
  if (data !== undefined) {
    const extra = typeof data === 'object' ? JSON.stringify(data) : data;
    return `${base} | ${extra}`;
  }
  return base;
}

export function makeLogger(context) {
  return {
    info: (msg, data) => console.log(format('INFO ', context, msg, data)),
    warn: (msg, data) => console.warn(format('WARN ', context, msg, data)),
    error: (msg, data) => console.error(format('ERROR', context, msg, data))
  };
}
