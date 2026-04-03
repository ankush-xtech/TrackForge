import { create } from "zustand";
import { apiClient } from "@/lib/api-client";

export interface TimeEntry {
  id: string;
  user_id: string;
  project_id: string | null;
  task_id: string | null;
  start_time: string;
  end_time: string | null;
  duration_seconds: number;
  activity_percent: number;
  mouse_events: number;
  keyboard_events: number;
  is_manual: boolean;
  description: string | null;
  created_at: string;
}

export interface TrackingSummary {
  today_seconds: number;
  week_seconds: number;
  month_seconds: number;
  entries_today: number;
  avg_activity_percent: number;
  is_tracking: boolean;
  active_entry_id: string | null;
}

interface TimeTrackingState {
  // Data
  activeEntry: TimeEntry | null;
  entries: TimeEntry[];
  summary: TrackingSummary | null;

  // UI state
  isLoading: boolean;
  error: string | null;
  elapsed: number; // live elapsed seconds for the timer display

  // Actions
  fetchActiveEntry: () => Promise<void>;
  fetchEntries: (params?: {
    date_from?: string;
    date_to?: string;
    project_id?: string;
  }) => Promise<void>;
  fetchSummary: () => Promise<void>;
  startTimer: (data: {
    project_id?: string;
    task_id?: string;
    description?: string;
  }) => Promise<void>;
  stopTimer: () => Promise<void>;
  deleteEntry: (entryId: string) => Promise<void>;
  setElapsed: (seconds: number) => void;
  clearError: () => void;
}

export const useTimeTrackingStore = create<TimeTrackingState>((set, get) => ({
  activeEntry: null,
  entries: [],
  summary: null,
  isLoading: false,
  error: null,
  elapsed: 0,

  clearError: () => set({ error: null }),

  setElapsed: (seconds: number) => set({ elapsed: seconds }),

  fetchActiveEntry: async () => {
    try {
      const res = await apiClient.get("/tracking/time-entries/active");
      set({ activeEntry: res.data || null });
    } catch {
      set({ activeEntry: null });
    }
  },

  fetchEntries: async (params) => {
    set({ isLoading: true });
    try {
      const res = await apiClient.get("/tracking/time-entries", { params });
      set({ entries: res.data || [], error: null });
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || "Failed to load time entries",
      });
    } finally {
      set({ isLoading: false });
    }
  },

  fetchSummary: async () => {
    try {
      const res = await apiClient.get("/tracking/summary");
      set({ summary: res.data });
    } catch {
      // silently fail — stats are non-critical
    }
  },

  startTimer: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const res = await apiClient.post("/tracking/time-entries", {
        ...data,
        start_time: new Date().toISOString(),
      });
      set({ activeEntry: res.data, elapsed: 0 });
      // Refresh summary
      get().fetchSummary();
    } catch (err: any) {
      set({
        error:
          err.response?.data?.detail || "Failed to start timer",
      });
    } finally {
      set({ isLoading: false });
    }
  },

  stopTimer: async () => {
    const { activeEntry } = get();
    if (!activeEntry) return;

    set({ isLoading: true, error: null });
    try {
      await apiClient.patch(
        `/tracking/time-entries/${activeEntry.id}/stop`,
        { end_time: new Date().toISOString() }
      );
      set({ activeEntry: null, elapsed: 0 });
      // Refresh entries and summary
      get().fetchEntries();
      get().fetchSummary();
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || "Failed to stop timer",
      });
    } finally {
      set({ isLoading: false });
    }
  },

  deleteEntry: async (entryId: string) => {
    try {
      await apiClient.delete(`/tracking/time-entries/${entryId}`);
      set((state) => ({
        entries: state.entries.filter((e) => e.id !== entryId),
      }));
      get().fetchSummary();
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || "Failed to delete entry",
      });
    }
  },
}));
