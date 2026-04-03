/**
 * WebWork Desktop Agent — Electron Main Process
 *
 * Responsibilities:
 * - System tray icon with start/stop tracking
 * - Screenshot capture at configurable intervals
 * - Activity monitoring (mouse/keyboard events)
 * - Active window detection
 * - Sync data to backend API
 * - Offline queue for when internet is unavailable
 */

import { app, BrowserWindow, Tray, Menu, nativeImage } from "electron";
import path from "path";

// Prevent multiple instances
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
}

let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;
let isTracking = false;

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 380,
    height: 520,
    resizable: false,
    frame: false,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "../preload/index.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // Load renderer
  if (process.env.NODE_ENV === "development") {
    mainWindow.loadURL("http://localhost:5173");
  } else {
    mainWindow.loadFile(path.join(__dirname, "../renderer/index.html"));
  }

  // Hide instead of close
  mainWindow.on("close", (event) => {
    event.preventDefault();
    mainWindow?.hide();
  });
}

function createTray(): void {
  // Placeholder icon — replace with actual icon in production
  const icon = nativeImage.createEmpty();
  tray = new Tray(icon);

  const contextMenu = Menu.buildFromTemplate([
    {
      label: "Open WebWork",
      click: () => mainWindow?.show(),
    },
    { type: "separator" },
    {
      label: isTracking ? "Stop Tracking" : "Start Tracking",
      click: () => toggleTracking(),
    },
    { type: "separator" },
    {
      label: "Quit",
      click: () => {
        mainWindow?.destroy();
        app.quit();
      },
    },
  ]);

  tray.setToolTip("WebWork Agent");
  tray.setContextMenu(contextMenu);

  tray.on("click", () => {
    mainWindow?.show();
  });
}

function toggleTracking(): void {
  isTracking = !isTracking;
  console.log(`Tracking ${isTracking ? "started" : "stopped"}`);

  if (isTracking) {
    startTracking();
  } else {
    stopTracking();
  }

  // Rebuild tray menu to update label
  createTray();
}

function startTracking(): void {
  // TODO: Implement in Milestone 3
  // - Start screenshot timer
  // - Start activity monitoring (mouse/keyboard)
  // - Start active window polling
  // - Create time entry via API
  console.log("Starting tracking session...");
}

function stopTracking(): void {
  // TODO: Implement in Milestone 3
  // - Stop all timers
  // - Flush remaining data to API
  // - Stop time entry via API
  console.log("Stopping tracking session...");
}

// App lifecycle
app.whenReady().then(() => {
  createWindow();
  createTray();

  // Auto-start tracking if configured
  console.log("WebWork Agent is ready");
});

app.on("window-all-closed", () => {
  // Don't quit on macOS — keep running in tray
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
