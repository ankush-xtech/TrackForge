"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { apiClient } from "@/lib/api-client";

interface UseScreenshotCaptureOptions {
  /** Capture interval in milliseconds (default: ~3m20s = 3 per 10 min) */
  interval?: number;
  /** Whether capture is active (only when timer is running) */
  enabled?: boolean;
  /** The active time entry ID to associate screenshots with */
  timeEntryId?: string | null;
  /** Called after a successful capture */
  onCapture?: () => void;
}

interface ScreenshotCaptureState {
  /** Whether we have screen share permission */
  hasPermission: boolean;
  /** Whether a capture is in progress */
  isCapturing: boolean;
  /** Total screenshots taken this session */
  captureCount: number;
  /** Request screen share permission */
  requestPermission: () => Promise<boolean>;
  /** Stop screen sharing */
  stopCapture: () => void;
}

export function useScreenshotCapture({
  interval = 200 * 1000, // ~3m20s → 3 screenshots per 10 minutes
  enabled = false,
  timeEntryId = null,
  onCapture,
}: UseScreenshotCaptureOptions): ScreenshotCaptureState {
  const [hasPermission, setHasPermission] = useState(false);
  const [isCapturing, setIsCapturing] = useState(false);
  const [captureCount, setCaptureCount] = useState(0);

  const streamRef = useRef<MediaStream | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const onCaptureRef = useRef(onCapture);
  onCaptureRef.current = onCapture;

  const captureFrame = useCallback(async () => {
    if (!streamRef.current || !timeEntryId) return;

    const track = streamRef.current.getVideoTracks()[0];
    if (!track || track.readyState !== "live") {
      // Stream ended (user revoked permission)
      setHasPermission(false);
      streamRef.current = null;
      return;
    }

    setIsCapturing(true);
    try {
      // Create a video element to draw the frame
      const video = document.createElement("video");
      video.srcObject = streamRef.current;
      video.muted = true;

      await new Promise<void>((resolve) => {
        video.onloadedmetadata = () => {
          video.play();
          resolve();
        };
      });

      // Wait a frame for the video to render
      await new Promise((r) => requestAnimationFrame(r));

      // Draw to canvas
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.drawImage(video, 0, 0);

      // Stop the video element (not the stream)
      video.pause();
      video.srcObject = null;

      // Convert to blob
      const blob = await new Promise<Blob | null>((resolve) =>
        canvas.toBlob(resolve, "image/jpeg", 0.7)
      );
      if (!blob) return;

      // Upload to backend
      const formData = new FormData();
      formData.append("file", blob, `screenshot-${Date.now()}.jpg`);
      formData.append("time_entry_id", timeEntryId);
      formData.append("captured_at", new Date().toISOString());

      await apiClient.post("/activity/screenshots/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setCaptureCount((prev) => prev + 1);
      onCaptureRef.current?.();
    } catch (err) {
      console.warn("Screenshot capture failed:", err);
    } finally {
      setIsCapturing(false);
    }
  }, [timeEntryId]);

  const requestPermission = useCallback(async (): Promise<boolean> => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: { displaySurface: "monitor" } as any,
        audio: false,
      });

      streamRef.current = stream;
      setHasPermission(true);

      // Listen for user stopping the share
      stream.getVideoTracks()[0].addEventListener("ended", () => {
        setHasPermission(false);
        streamRef.current = null;
      });

      return true;
    } catch {
      setHasPermission(false);
      return false;
    }
  }, []);

  const stopCapture = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setHasPermission(false);
    setCaptureCount(0);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // Auto-capture on interval when enabled + has permission
  useEffect(() => {
    if (enabled && hasPermission && timeEntryId) {
      // Capture immediately on start
      captureFrame();

      intervalRef.current = setInterval(captureFrame, interval);
      return () => {
        if (intervalRef.current) clearInterval(intervalRef.current);
      };
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
  }, [enabled, hasPermission, timeEntryId, interval, captureFrame]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  return { hasPermission, isCapturing, captureCount, requestPermission, stopCapture };
}