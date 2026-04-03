/**
 * Active window and application detection module.
 * Tracks which apps and websites the employee is using.
 */

// import activeWin from "active-win";

interface ActiveAppInfo {
  appName: string;
  windowTitle: string;
  url?: string; // Extracted from browser window titles
  timestamp: Date;
}

interface AppUsageRecord {
  appName: string;
  windowTitle: string;
  url?: string;
  startedAt: Date;
  endedAt?: Date;
  durationSeconds: number;
}

let pollTimer: NodeJS.Timeout | null = null;
let currentApp: ActiveAppInfo | null = null;
let usageLog: AppUsageRecord[] = [];

const BROWSER_APPS = [
  "google chrome",
  "firefox",
  "microsoft edge",
  "safari",
  "brave browser",
  "opera",
  "vivaldi",
];

export function startDetection(intervalMs: number = 5000): void {
  console.log(`App detection started (polling every ${intervalMs}ms)`);

  pollTimer = setInterval(async () => {
    try {
      await detectActiveWindow();
    } catch (error) {
      console.error("App detection failed:", error);
    }
  }, intervalMs);
}

export function stopDetection(): AppUsageRecord[] {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }

  // Close current app record
  if (currentApp) {
    closeCurrentRecord();
  }

  const log = [...usageLog];
  usageLog = [];
  console.log(`App detection stopped. ${log.length} records collected.`);
  return log;
}

async function detectActiveWindow(): Promise<void> {
  // TODO: Implement with active-win package in Milestone 3
  // const result = await activeWin();
  // if (!result) return;
  //
  // const info: ActiveAppInfo = {
  //   appName: result.owner.name,
  //   windowTitle: result.title,
  //   url: extractUrl(result.owner.name, result.title),
  //   timestamp: new Date(),
  // };
  //
  // handleWindowChange(info);

  // Placeholder for development
  console.log("Polling active window...");
}

function handleWindowChange(info: ActiveAppInfo): void {
  if (currentApp && currentApp.appName === info.appName && currentApp.windowTitle === info.windowTitle) {
    return; // Same window, no change
  }

  // Close previous record
  if (currentApp) {
    closeCurrentRecord();
  }

  // Start new record
  currentApp = info;
  usageLog.push({
    appName: info.appName,
    windowTitle: info.windowTitle,
    url: info.url,
    startedAt: info.timestamp,
    durationSeconds: 0,
  });
}

function closeCurrentRecord(): void {
  if (usageLog.length > 0) {
    const last = usageLog[usageLog.length - 1];
    last.endedAt = new Date();
    last.durationSeconds = Math.floor(
      (last.endedAt.getTime() - last.startedAt.getTime()) / 1000
    );
  }
  currentApp = null;
}

function extractUrl(appName: string, windowTitle: string): string | undefined {
  const isABrowser = BROWSER_APPS.some((b) =>
    appName.toLowerCase().includes(b)
  );
  if (!isABrowser) return undefined;

  // Try to extract URL from window title (browsers often show "Page Title - URL")
  // This is browser-specific and will need refinement
  const urlMatch = windowTitle.match(
    /https?:\/\/[^\s]+/
  );
  return urlMatch ? urlMatch[0] : undefined;
}

export function flushUsageLog(): AppUsageRecord[] {
  const log = [...usageLog];
  usageLog = [];
  return log;
}
