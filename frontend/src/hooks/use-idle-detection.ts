"use client";

import { useEffect, useRef, useCallback, useState } from "react";

interface UseIdleDetectionOptions {
  /** Idle timeout in milliseconds (default: 5 minutes) */
  timeout?: number;
  /** Whether detection is active (only when timer is running) */
  enabled?: boolean;
  /** Called when user goes idle */
  onIdle?: () => void;
  /** Called when user resumes activity after being idle */
  onActive?: () => void;
}

interface IdleDetectionState {
  isIdle: boolean;
  idleSince: Date | null;
  /** Seconds the user has been idle */
  idleSeconds: number;
}

export function useIdleDetection({
  timeout = 5 * 60 * 1000, // 5 minutes
  enabled = false,
  onIdle,
  onActive,
}: UseIdleDetectionOptions): IdleDetectionState {
  const [isIdle, setIsIdle] = useState(false);
  const [idleSince, setIdleSince] = useState<Date | null>(null);
  const [idleSeconds, setIdleSeconds] = useState(0);

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const idleTickRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const onIdleRef = useRef(onIdle);
  const onActiveRef = useRef(onActive);
  const isIdleRef = useRef(false);

  // Keep callback refs fresh
  onIdleRef.current = onIdle;
  onActiveRef.current = onActive;

  const resetTimer = useCallback(() => {
    // If user was idle, mark them active again
    if (isIdleRef.current) {
      isIdleRef.current = false;
      setIsIdle(false);
      setIdleSince(null);
      setIdleSeconds(0);
      if (idleTickRef.current) {
        clearInterval(idleTickRef.current);
        idleTickRef.current = null;
      }
      onActiveRef.current?.();
    }

    // Reset the idle countdown
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    timerRef.current = setTimeout(() => {
      // User has been inactive for `timeout` ms
      isIdleRef.current = true;
      const now = new Date();
      setIsIdle(true);
      setIdleSince(now);
      setIdleSeconds(0);
      onIdleRef.current?.();

      // Start counting idle seconds
      idleTickRef.current = setInterval(() => {
        setIdleSeconds((prev) => prev + 1);
      }, 1000);
    }, timeout);
  }, [timeout]);

  useEffect(() => {
    if (!enabled) {
      // Clean up everything when disabled
      if (timerRef.current) clearTimeout(timerRef.current);
      if (idleTickRef.current) clearInterval(idleTickRef.current);
      setIsIdle(false);
      setIdleSince(null);
      setIdleSeconds(0);
      isIdleRef.current = false;
      return;
    }

    // Events that indicate user activity
    const events = [
      "mousemove",
      "mousedown",
      "keydown",
      "touchstart",
      "scroll",
      "wheel",
      "click",
    ];

    const handleActivity = () => {
      resetTimer();
    };

    events.forEach((event) => {
      document.addEventListener(event, handleActivity, { passive: true });
    });

    // Start the initial timer
    resetTimer();

    return () => {
      events.forEach((event) => {
        document.removeEventListener(event, handleActivity);
      });
      if (timerRef.current) clearTimeout(timerRef.current);
      if (idleTickRef.current) clearInterval(idleTickRef.current);
    };
  }, [enabled, resetTimer]);

  return { isIdle, idleSince, idleSeconds };
}