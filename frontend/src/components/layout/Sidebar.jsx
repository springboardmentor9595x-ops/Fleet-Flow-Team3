import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Truck,
  Users,
  Package,
  Map,
  Wrench,
  Fuel,
  Bell,
  ClipboardCheck,
  LogOut,
} from "lucide-react";

import { useAuth } from "../../context/AuthContext";

export default function Sidebar() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const menuItems = [
    {
      name: "Dashboard",
      path: "/dashboard",
      icon: LayoutDashboard,
    },
    {
      name: "Vehicles",
      path: "/vehicles",
      icon: Truck,
    },
    {
      name: "Drivers",
      path: "/drivers",
      icon: Users,
    },
    {
      name: "Shipments",
      path: "/shipments",
      icon: Package,
    },
    {
      name: "Trips",
      path: "/trips",
      icon: Map,
    },
    {
      name: "Maintenance",
      path: "/maintenance",
      icon: Wrench,
    },
    {
      name: "Fuel Records",
      path: "/fuel",
      icon: Fuel,
    },
    {
      name: "Notifications",
      path: "/notifications",
      icon: Bell,
    },
    {
      name: "Attendance",
      path: "/attendance",
      icon: ClipboardCheck,
    },
  ];

  return (
    <aside style={styles.sidebar}>
      <div style={styles.logo}>
        <Truck size={30} />
        <span>FleetFlow</span>
      </div>

      <nav style={styles.nav}>
        {menuItems.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                ...styles.link,
                ...(isActive ? styles.activeLink : {}),
              })}
            >
              <Icon size={20} />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      <button onClick={handleLogout} style={styles.logout}>
        <LogOut size={20} />
        <span>Logout</span>
      </button>
    </aside>
  );
}

const styles = {
  sidebar: {
    width: "250px",
    minHeight: "100vh",
    background: "#172554",
    color: "white",
    display: "flex",
    flexDirection: "column",
    position: "fixed",
    left: 0,
    top: 0,
    bottom: 0,
  },

  logo: {
    height: "75px",
    display: "flex",
    alignItems: "center",
    gap: "12px",
    padding: "0 25px",
    fontSize: "24px",
    fontWeight: "700",
    borderBottom: "1px solid rgba(255,255,255,0.1)",
  },

  nav: {
    padding: "20px 12px",
    display: "flex",
    flexDirection: "column",
    gap: "5px",
  },

  link: {
    display: "flex",
    alignItems: "center",
    gap: "13px",
    padding: "12px 15px",
    borderRadius: "8px",
    color: "#cbd5e1",
    textDecoration: "none",
    fontSize: "15px",
    transition: "0.2s",
  },

  activeLink: {
    background: "#2563eb",
    color: "white",
  },

  logout: {
    margin: "auto 12px 25px",
    padding: "12px 15px",
    display: "flex",
    alignItems: "center",
    gap: "13px",
    border: "none",
    borderRadius: "8px",
    background: "#dc2626",
    color: "white",
    fontSize: "15px",
    cursor: "pointer",
  },
};