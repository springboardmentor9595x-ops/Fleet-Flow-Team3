import { useContext, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../context/auth-context";
import NotificationBell from "./NotificationBell";

function Navbar() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const initials = (user?.full_name || "FleetFlow User").split(" ").map((word) => word[0]).join("").slice(0, 2).toUpperCase();
  const signOut = () => { logout(); navigate("/login", { replace: true }); };
  return <header className="app-navbar"><div className="navbar-breadcrumb">FleetFlow / <strong>Operations</strong></div><div className="navbar-actions"><NotificationBell /><div className="navbar-profile"><button className="profile-button" onClick={() => setOpen((value) => !value)}><b>{initials}</b><span>{user?.full_name || "FleetFlow User"}<small>{user?.role || "User"}</small></span>⌄</button>{open && <div className="profile-menu"><button onClick={() => navigate("/profile")}>Profile</button><button onClick={() => navigate("/profile")}>Change Password</button><button onClick={signOut}>Logout</button><button className="danger" onClick={signOut}>Sign Out</button></div>}</div></div></header>;
}

export default Navbar;
