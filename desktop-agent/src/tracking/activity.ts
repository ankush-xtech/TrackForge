/**
 * Activity monitoring module.
 * Tracks mouse movements, keyboard events, and idle time.
 */

interface ActivityData {
  mouseEvents: number;
  keyboardEvents: number;
  mouseDistance: number;
  scrollEvents: number;
  clickEvents: number;
  intervalStart: Date;
  intervalEnd: Date;
}

interface ActivityConfig {
  intervalMs: number; // How often to sample and send data
  idleThresholdMs: number; // Time without input to consider idle
}

const DEFAULT_CONFIG: ActivityConfig = {
  intervalMs: 60 * 1000, // 1 minute
  idleThresholdMs: 5 * 60 * 1000, // 5 minutes
};

let activityTimer: NodeJS.Timeout | null = null;
let currentData: ActivityData = createEmptyData();
let lastInputTime = Date.now();

function createEmptyData(): ActivityData {
  return {
    mouseEvents: 0,
    keyboardEvents: 0,
    mouseDistance: 0,
    scrollEvents: 0,
    clickEvents: 0,
    intervalStart: new Date(),
    intervalEnd: new Date(),
  };
}

export function startMonitoring(config?: Partial<ActivityConfig>): void {
  const cfg = { ...DEFAULT_CONFIG, ...config };

  console.log(`Activity monitoring started (interval: ${cfg.intervalMs}ms)`);

  // TODO: Hook into actual mouse/keyboard events via uiohook-napi in Milestone 3
  // const { uIOhook, UiohookKey } = require("uiohook-napi");
  //
  // uIOhook.on("mousemove", (e) => {
  //   currentData.mouseEvents++;
  //   lastInputTime = Date.now();
  // });
  //
  // uIOhook.on("keydown", (e) => {
  //   currentData.keyboardEvents++;
  //   lastInputTime = Date.now();
  // });
  //
  // uIOhook.start();

  // Periodic flush
  activityTimer = setInterval(() => {
    const data = flushData();
    sendActivityData(data);
  }, cfg.intervalMs);
}

export function stopMonitoring(): void {
  if (activityTimer) {
    clearInterval(activityTimer);
    activityTimer = null;
  }
  // Flush remaining data
  const remaining = flushData();
  if (remaining.mouseEvents > 0 || remaining.keyboardEvents > 0) {
    sendActivityData(remaining);
  }
  console.log("Activity monitoring stopped");
}

function flushData(): ActivityData {
  const data = { ...currentData, intervalEnd: new Date() };
  currentData = createEmptyData();
  return data;
}

function calculateActivityPercent(data: ActivityData): number {
  const durationMs =
    data.intervalEnd.getTime() - data.intervalStart.getTime();
  if (durationMs === 0) return 0;

  // Activity = percentage of seconds with at least one input event
  // Simplified: use event count as a proxy
  const totalEvents = data.mouseEvents + data.keyboardEvents;
  const durationSeconds = durationMs / 1000;
  const eventsPerSecond = totalEvents / durationSeconds;

  // Normalize: 1+ events per second = 100% activity
  return Math.min(eventsPerSecond * 100, 100);
}

async function sendActivityData(data: ActivityData): Promise<void> {
  // TODO: Send to API via tracking/sync endpoint in Milestone 3
  const percent = calculateActivityPercent(data);
  console.log(
    `Activity: ${data.mouseEvents} mouse, ${data.keyboardEvents} keyboard, ${percent.toFixed(1)}%`
  );
}

export function isIdle(): boolean {
  return Date.now() - lastInputTime > DEFAULT_CONFIG.idleThresholdMs;
}
