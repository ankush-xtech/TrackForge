/**
 * Screenshot capture module.
 * Takes periodic screenshots and queues them for upload.
 */

// import screenshot from "screenshot-desktop";
// import { apiClient } from "./api";

interface ScreenshotConfig {
  intervalMs: number; // Capture interval in milliseconds
  quality: number; // JPEG quality (1-100)
  maxWidth: number; // Max width to resize to
  blurEnabled: boolean; // Whether to blur screenshots
}

const DEFAULT_CONFIG: ScreenshotConfig = {
  intervalMs: 5 * 60 * 1000, // 5 minutes
  quality: 70,
  maxWidth: 1920,
  blurEnabled: false,
};

let captureTimer: NodeJS.Timeout | null = null;
let config = { ...DEFAULT_CONFIG };

export function startCapture(customConfig?: Partial<ScreenshotConfig>): void {
  if (customConfig) {
    config = { ...DEFAULT_CONFIG, ...customConfig };
  }

  console.log(`Screenshot capture started (interval: ${config.intervalMs}ms)`);

  captureTimer = setInterval(async () => {
    try {
      await captureScreenshot();
    } catch (error) {
      console.error("Screenshot capture failed:", error);
    }
  }, config.intervalMs);
}

export function stopCapture(): void {
  if (captureTimer) {
    clearInterval(captureTimer);
    captureTimer = null;
  }
  console.log("Screenshot capture stopped");
}

async function captureScreenshot(): Promise<void> {
  // TODO: Implement in Milestone 3
  // 1. Capture screenshot using screenshot-desktop
  // 2. Resize if larger than maxWidth
  // 3. Compress to target quality
  // 4. Apply blur if enabled
  // 5. Save to local queue
  // 6. Upload to API when online
  console.log(`Screenshot captured at ${new Date().toISOString()}`);
}

export function updateConfig(newConfig: Partial<ScreenshotConfig>): void {
  config = { ...config, ...newConfig };
  // Restart capture with new config if currently running
  if (captureTimer) {
    stopCapture();
    startCapture();
  }
}
