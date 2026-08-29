import { useCallback, useContext, useEffect, useRef, useState } from "react";
import { AuthContext } from "../context/auth-context";
import api from "../services/api";
import "./NotificationBell.css";

const POLL_INTERVAL_MS = 45_000;

function notificationErrorMessage(error) {
  const status = error?.response?.status;
  if (status === 401) return "Your session has expired. Please sign in again.";
  if (status === 403) return "You do not have permission to view notifications.";
  return "Unable to load notifications. Please try again.";
}

function formatNotificationTime(value) {
  if (!value) return "Just now";
  const timestamp = new Date(value);
  if (Number.isNaN(timestamp.getTime())) return "Unknown time";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(timestamp);
}

function NotificationBell() {
  const { token } = useContext(AuthContext);
  const rootRef = useRef(null);
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [updatingId, setUpdatingId] = useState("");
  const [markingAll, setMarkingAll] = useState(false);

  const refreshUnreadCount = useCallback(async (showError = false) => {
    if (!token) return;
    try {
      const response = await api.get("/notifications", {
        params: { unread_only: true, limit: 100 },
      });
      setUnreadCount(response.data.length);
      if (showError) setError("");
    } catch (requestError) {
      // Polling remains silent so temporary network issues do not repeatedly
      // interrupt the user. The open panel displays a useful error instead.
      if (showError) setError(notificationErrorMessage(requestError));
    }
  }, [token]);

  const loadNotifications = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const response = await api.get("/notifications", { params: { limit: 50 } });
      setNotifications(response.data);
    } catch (requestError) {
      setError(notificationErrorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (!token) return undefined;
    const initialRefreshId = window.setTimeout(() => refreshUnreadCount(), 0);
    const intervalId = window.setInterval(() => refreshUnreadCount(), POLL_INTERVAL_MS);
    return () => {
      window.clearTimeout(initialRefreshId);
      window.clearInterval(intervalId);
    };
  }, [token, refreshUnreadCount]);

  useEffect(() => {
    if (!open) return undefined;
    // Defer the panel refresh until after this render rather than synchronously
    // changing state from the effect body.
    const refreshId = window.setTimeout(() => {
      loadNotifications();
      refreshUnreadCount(true);
    }, 0);
    return () => window.clearTimeout(refreshId);
  }, [open, loadNotifications, refreshUnreadCount]);

  useEffect(() => {
    const closeOnOutsideClick = (event) => {
      if (rootRef.current && !rootRef.current.contains(event.target)) setOpen(false);
    };
    const closeOnEscape = (event) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", closeOnOutsideClick);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOnOutsideClick);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, []);

  const markAsRead = async (notification) => {
    if (notification.is_read || updatingId || markingAll) return;
    setUpdatingId(notification.notification_id);
    setError("");
    try {
      const response = await api.patch(`/notifications/${notification.notification_id}/read`);
      setNotifications((current) => current.map((item) => (
        item.notification_id === notification.notification_id ? response.data : item
      )));
      setUnreadCount((current) => Math.max(0, current - 1));
    } catch (requestError) {
      setError(notificationErrorMessage(requestError));
    } finally {
      setUpdatingId("");
    }
  };

  const markAllAsRead = async () => {
    if (!unreadCount || markingAll || updatingId) return;
    setMarkingAll(true);
    setError("");
    try {
      await api.patch("/notifications/read-all");
      setNotifications((current) => current.map((item) => ({ ...item, is_read: true })));
      setUnreadCount(0);
    } catch (requestError) {
      setError(notificationErrorMessage(requestError));
    } finally {
      setMarkingAll(false);
    }
  };

  const badgeText = unreadCount > 99 ? "99+" : unreadCount;

  return (
    <div className="notification-center" ref={rootRef}>
      <button
        type="button"
        className="notification-bell"
        aria-label={unreadCount ? `Notifications, ${unreadCount} unread` : "Notifications"}
        aria-expanded={open}
        aria-haspopup="dialog"
        onClick={() => setOpen((current) => !current)}
      >
        <span aria-hidden="true">🔔</span>
        {unreadCount > 0 && <span className="notification-count">{badgeText}</span>}
      </button>

      {open && (
        <section className="notification-panel" role="dialog" aria-label="Notifications">
          <header className="notification-panel-header">
            <div>
              <h2>Notifications</h2>
              {unreadCount > 0 && <p>{unreadCount} unread</p>}
            </div>
            <button
              type="button"
              className="notification-read-all"
              onClick={markAllAsRead}
              disabled={!unreadCount || markingAll || Boolean(updatingId)}
            >
              {markingAll ? "Marking…" : "Mark all as read"}
            </button>
          </header>

          {error && <p className="notification-error" role="alert">{error}</p>}

          <div className="notification-list" aria-busy={loading}>
            {loading && <p className="notification-loading">Loading notifications…</p>}
            {!loading && !error && notifications.length === 0 && (
              <div className="notification-empty"><span aria-hidden="true">🔔</span><p>No notifications yet</p></div>
            )}
            {!loading && notifications.map((notification) => (
              <button
                type="button"
                key={notification.notification_id}
                className={`notification-item ${notification.is_read ? "is-read" : "is-unread"}`}
                onClick={() => markAsRead(notification)}
                disabled={notification.is_read || updatingId === notification.notification_id || markingAll}
                aria-label={`${notification.is_read ? "Read" : "Unread"}: ${notification.title}`}
              >
                <span className="notification-item-dot" aria-hidden="true" />
                <span className="notification-item-content">
                  <strong>{notification.title}</strong>
                  <span>{notification.message}</span>
                  <time dateTime={notification.created_at}>{formatNotificationTime(notification.created_at)}</time>
                </span>
                {updatingId === notification.notification_id && <span className="notification-item-saving">Saving…</span>}
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export default NotificationBell;
