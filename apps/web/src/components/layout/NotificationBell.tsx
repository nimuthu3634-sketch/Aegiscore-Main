import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState
} from "react";
import { useNavigate } from "react-router-dom";
import {
  fetchRecentNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  type RecentNotificationItem
} from "../../lib/api";
import type { IconName } from "../../lib/theme/tokens";
import { Button } from "../ui/Button";
import { Icon } from "../ui/Icon";
import { cn } from "../../lib/cn";

const DEFAULT_POLL_MS = 30_000;

function formatRelativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) {
    return "";
  }
  const now = Date.now();
  const sec = Math.floor((now - then) / 1000);
  if (sec < 45) {
    return "just now";
  }
  if (sec < 3600) {
    const m = Math.floor(sec / 60);
    return `${m}m ago`;
  }
  if (sec < 86400) {
    const h = Math.floor(sec / 3600);
    return `${h}h ago`;
  }
  const startOfToday = new Date();
  startOfToday.setHours(0, 0, 0, 0);
  const startOfYesterday = new Date(startOfToday);
  startOfYesterday.setDate(startOfYesterday.getDate() - 1);
  if (then >= startOfYesterday.getTime() && then < startOfToday.getTime()) {
    return "yesterday";
  }
  const d = new Date(then);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function triggerIconName(triggerType: string): IconName {
  switch (triggerType) {
    case "risk_threshold":
      return "warning";
    case "incident_state":
      return "activity";
    case "response_result":
      return "responses";
    case "notify_admin":
      return "shield";
    default:
      return "spark";
  }
}

function formatTriggerLabel(triggerType: string): string {
  return triggerType.replace(/_/g, " ");
}

type NotificationBellProps = {
  pollIntervalMs?: number;
};

export function NotificationBell({
  pollIntervalMs = DEFAULT_POLL_MS
}: NotificationBellProps) {
  const navigate = useNavigate();
  const menuId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [listLoading, setListLoading] = useState(false);
  const [items, setItems] = useState<RecentNotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [toast, setToast] = useState<string | null>(null);
  const prevUnreadIdsRef = useRef<Set<string> | null>(null);
  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const dismissToast = useCallback(() => {
    if (toastTimerRef.current) {
      clearTimeout(toastTimerRef.current);
      toastTimerRef.current = null;
    }
    setToast(null);
  }, []);

  const showToast = useCallback(
    (message: string) => {
      dismissToast();
      setToast(message);
      toastTimerRef.current = setTimeout(() => {
        setToast(null);
        toastTimerRef.current = null;
      }, 5000);
    },
    [dismissToast]
  );

  const pollUnread = useCallback(async () => {
    try {
      const data = await fetchRecentNotifications({ limit: 5, unreadOnly: true });
      setUnreadCount(data.unread_count);
      const ids = new Set(data.items.map((i) => i.id));
      const prev = prevUnreadIdsRef.current;
      if (prev !== null) {
        for (const item of data.items) {
          if (!prev.has(item.id)) {
            showToast(item.subject);
            break;
          }
        }
      }
      prevUnreadIdsRef.current = ids;
    } catch {
      /* ignore poll errors */
    }
  }, [showToast]);

  useEffect(() => {
    void pollUnread();
    const id = window.setInterval(() => void pollUnread(), pollIntervalMs);
    return () => window.clearInterval(id);
  }, [pollUnread, pollIntervalMs]);

  useEffect(() => {
    return () => {
      if (toastTimerRef.current) {
        clearTimeout(toastTimerRef.current);
      }
    };
  }, []);

  const loadDropdownList = useCallback(async () => {
    setListLoading(true);
    try {
      const data = await fetchRecentNotifications({ limit: 20, unreadOnly: false });
      setItems(data.items);
      setUnreadCount(data.unread_count);
    } catch {
      setItems([]);
    } finally {
      setListLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      void loadDropdownList();
    }
  }, [open, loadDropdownList]);

  useEffect(() => {
    if (!open) {
      return undefined;
    }
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open]);

  useEffect(() => {
    if (!open) {
      return undefined;
    }
    const onPointerDown = (e: MouseEvent | TouchEvent) => {
      const el = rootRef.current;
      if (el && !el.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("touchstart", onPointerDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("touchstart", onPointerDown);
    };
  }, [open]);

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      await loadDropdownList();
      void pollUnread();
    } catch {
      /* ignore */
    }
  };

  const handleRowClick = async (item: RecentNotificationItem) => {
    try {
      if (!item.read) {
        await markNotificationRead(item.id);
      }
      setOpen(false);
      navigate(`/incidents/${item.incident_id}`);
      void pollUnread();
    } catch {
      /* still navigate */
      setOpen(false);
      navigate(`/incidents/${item.incident_id}`);
    }
  };

  return (
    <>
      {toast ? (
        <div
          className="pointer-events-none fixed left-1/2 top-4 z-[60] w-[min(28rem,calc(100vw-2rem))] -translate-x-1/2 px-3"
          role="status"
          aria-live="polite"
        >
          <div className="pointer-events-auto rounded-field border border-border-subtle bg-white px-4 py-3 shadow-lg">
            <span className="font-semibold text-brand-primary">New notification</span>
            <p className="mt-1 line-clamp-2 text-body-sm text-content-secondary">{toast}</p>
            <button
              type="button"
              className="mt-2 text-label-sm font-semibold text-brand-primary hover:text-brand-hover"
              onClick={dismissToast}
            >
              Dismiss
            </button>
          </div>
        </div>
      ) : null}
      <div className="relative" ref={rootRef}>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="relative shrink-0 text-content-secondary hover:text-brand-hover"
          aria-expanded={open}
          aria-haspopup="true"
          aria-controls={menuId}
          onClick={() => setOpen((v) => !v)}
          aria-label={
            unreadCount > 0
              ? `Notifications, ${unreadCount} unread`
              : "Notifications"
          }
        >
          <Icon name="bell" className="h-5 w-5" />
          {unreadCount > 0 ? (
            <>
              <span className="absolute right-0.5 top-0.5 z-[1] hidden h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-status-danger px-1 text-[10px] font-bold leading-none text-white md:inline-flex">
                {unreadCount > 99 ? "99+" : unreadCount}
              </span>
              <span
                className="absolute right-1 top-1 z-[1] h-2 w-2 rounded-full bg-status-danger md:hidden"
                aria-hidden
              />
            </>
          ) : null}
        </Button>
        {open ? (
          <div
            id={menuId}
            role="menu"
            className="absolute right-0 z-50 mt-2 w-[min(22rem,calc(100vw-2rem))] overflow-hidden rounded-field border border-border-subtle bg-white shadow-xl"
          >
            <div className="flex items-center justify-between gap-2 border-b border-border-subtle px-3 py-2.5">
              <p className="text-body-sm font-semibold text-content-primary">Notifications</p>
              <Button
                type="button"
                variant="quiet"
                size="sm"
                className="h-8 shrink-0 px-2 text-label-sm"
                onClick={() => void handleMarkAllRead()}
                disabled={unreadCount === 0}
              >
                Mark all read
              </Button>
            </div>
            <div className="max-h-[400px] overflow-y-auto">
              {listLoading ? (
                <p className="px-4 py-6 text-center text-body-sm text-content-muted">Loading…</p>
              ) : items.length === 0 ? (
                <p className="px-4 py-6 text-center text-body-sm text-content-muted">
                  No notifications yet
                </p>
              ) : (
                <ul className="divide-y divide-border-subtle">
                  {items.map((item) => (
                    <li key={item.id}>
                      <button
                        type="button"
                        role="menuitem"
                        onClick={() => void handleRowClick(item)}
                        className={cn(
                          "flex w-full gap-3 px-3 py-3 text-left transition hover:bg-surface-subtle/80",
                          !item.read
                            ? "border-l-[3px] border-l-brand-primary bg-brand-primary/[0.04]"
                            : "border-l-[3px] border-l-transparent opacity-80"
                        )}
                      >
                        <span
                          className={cn(
                            "mt-0.5 shrink-0",
                            item.read ? "text-content-muted" : "text-brand-primary"
                          )}
                        >
                          <Icon name={triggerIconName(item.trigger_type)} className="h-5 w-5" />
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="mb-1 inline-flex items-center gap-1.5">
                            <span className="rounded-chip border border-border-subtle bg-surface-subtle px-1.5 py-0.5 text-[11px] font-medium normal-case text-content-muted">
                              {formatTriggerLabel(item.trigger_type)}
                            </span>
                            {!item.read ? (
                              <span className="h-2 w-2 shrink-0 rounded-full bg-status-danger" title="Unread" />
                            ) : (
                              <span className="h-2 w-2 shrink-0 rounded-full bg-content-muted/40" title="Read" />
                            )}
                          </span>
                          <span className="line-clamp-2 text-body-sm font-medium text-content-primary">
                            {item.subject}
                          </span>
                          <span className="mt-0.5 block text-label-sm text-content-muted">
                            {formatRelativeTime(item.created_at)}
                          </span>
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="border-t border-border-subtle px-3 py-2 text-center">
              <button
                type="button"
                className="text-label-sm font-semibold text-brand-primary hover:text-brand-hover"
                onClick={() => {
                  setOpen(false);
                  navigate("/incidents");
                }}
              >
                View all incidents
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </>
  );
}
