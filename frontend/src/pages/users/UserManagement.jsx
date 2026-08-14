import { useEffect, useState } from "react";
import { Shield, User, Trash2, ChevronDown } from "lucide-react";
import Sidebar from "../../components/layout/Sidebar";
import api from "../../api/axios";
import { useAuth } from "../../context/AuthContext";

const ROLES = ["Admin", "FleetManager", "Dispatcher", "Driver"];

const ROLE_COLORS = {
  Admin: { bg: "#fef3c7", color: "#92400e" },
  FleetManager: { bg: "#dbeafe", color: "#1d4ed8" },
  Dispatcher: { bg: "#d1fae5", color: "#065f46" },
  Driver: { bg: "#f3e8ff", color: "#6b21a8" },
};

export default function UserManagement() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updatingId, setUpdatingId] = useState(null);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const res = await api.get("/users/");
      setUsers(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load users.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleRoleChange = async (userId, newRole) => {
    setUpdatingId(userId);
    try {
      await api.put(`/users/${userId}/role`, { role: newRole });
      setUsers((prev) =>
        prev.map((u) =>
          u.user_id === userId ? { ...u, role: newRole } : u
        )
      );
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to update role.");
    } finally {
      setUpdatingId(null);
    }
  };

  const handleDelete = async (userId) => {
    if (!window.confirm("Delete this user? This cannot be undone.")) return;
    try {
      await api.delete(`/users/${userId}`);
      setUsers((prev) => prev.filter((u) => u.user_id !== userId));
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete user.");
    }
  };

  const roleColor = (role) =>
    ROLE_COLORS[role] || { bg: "#f1f5f9", color: "#334155" };

  return (
    <div style={styles.app}>
      <Sidebar />

      <div style={styles.content}>
        <header style={styles.header}>
          <div>
            <h1 style={styles.title}>User Management</h1>
            <p style={styles.subtitle}>
              Manage all system users and their roles
            </p>
          </div>
        </header>

        <main style={styles.main}>
          {error && <div style={styles.errorBox}>{error}</div>}

          <div style={styles.tableCard}>
            {loading ? (
              <p style={styles.message}>Loading users...</p>
            ) : users.length === 0 ? (
              <p style={styles.message}>No users found.</p>
            ) : (
              <div style={styles.tableWrapper}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Phone</th>
                      <th>Role</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => {
                      const rc = roleColor(u.role);
                      const isSelf =
                        u.user_id === currentUser?.user_id;
                      return (
                        <tr key={u.user_id}>
                          <td>
                            <div style={styles.nameCell}>
                              <div style={styles.avatar}>
                                <User size={14} />
                              </div>
                              <strong>{u.full_name}</strong>
                              {isSelf && (
                                <span style={styles.youBadge}>
                                  You
                                </span>
                              )}
                            </div>
                          </td>
                          <td style={styles.emailCell}>{u.email}</td>
                          <td>{u.phone || "—"}</td>
                          <td>
                            <span
                              style={{
                                ...styles.roleBadge,
                                background: rc.bg,
                                color: rc.color,
                              }}
                            >
                              {u.role}
                            </span>
                          </td>
                          <td>
                            <div style={styles.actions}>
                              {/* Role select */}
                              <select
                                value={u.role}
                                onChange={(e) =>
                                  handleRoleChange(
                                    u.user_id,
                                    e.target.value
                                  )
                                }
                                disabled={
                                  isSelf ||
                                  updatingId === u.user_id
                                }
                                style={styles.roleSelect}
                              >
                                {ROLES.map((r) => (
                                  <option key={r} value={r}>
                                    {r}
                                  </option>
                                ))}
                              </select>

                              {/* Delete */}
                              {!isSelf && (
                                <button
                                  style={styles.deleteBtn}
                                  onClick={() =>
                                    handleDelete(u.user_id)
                                  }
                                  title="Delete user"
                                >
                                  <Trash2 size={15} />
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

const styles = {
  app: { minHeight: "100vh", background: "#f4f7fb" },
  content: { marginLeft: "250px", minHeight: "100vh" },
  header: {
    padding: "25px 40px",
    background: "white",
    borderBottom: "1px solid #e5e7eb",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  title: { margin: 0, fontSize: "26px", fontWeight: "700", color: "#172554" },
  subtitle: { marginTop: "5px", color: "#64748b", fontSize: "14px" },
  main: { padding: "30px 40px" },
  errorBox: {
    background: "#fee2e2",
    color: "#991b1b",
    padding: "14px 18px",
    borderRadius: "8px",
    marginBottom: "20px",
  },
  tableCard: {
    background: "white",
    borderRadius: "12px",
    boxShadow: "0 4px 15px rgba(0,0,0,0.05)",
    overflow: "hidden",
  },
  tableWrapper: { overflowX: "auto" },
  table: { width: "100%", borderCollapse: "collapse" },
  message: { padding: "30px", textAlign: "center", color: "#64748b" },
  nameCell: { display: "flex", alignItems: "center", gap: "10px" },
  avatar: {
    width: "30px",
    height: "30px",
    borderRadius: "50%",
    background: "#dbeafe",
    color: "#1d4ed8",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },
  emailCell: { color: "#64748b", fontSize: "13px" },
  youBadge: {
    fontSize: "11px",
    background: "#dcfce7",
    color: "#166534",
    padding: "2px 7px",
    borderRadius: "10px",
    fontWeight: "600",
  },
  roleBadge: {
    display: "inline-block",
    padding: "4px 10px",
    borderRadius: "12px",
    fontSize: "12px",
    fontWeight: "600",
  },
  actions: { display: "flex", alignItems: "center", gap: "8px" },
  roleSelect: {
    padding: "6px 10px",
    borderRadius: "6px",
    border: "1px solid #cbd5e1",
    fontSize: "13px",
    cursor: "pointer",
    background: "white",
  },
  deleteBtn: {
    padding: "6px 10px",
    borderRadius: "6px",
    border: "none",
    background: "#fee2e2",
    color: "#dc2626",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
  },
};
