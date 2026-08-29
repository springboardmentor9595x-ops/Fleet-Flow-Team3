import { useContext } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { AuthContext } from "../context/auth-context";

const navigationByRole = {
  Admin: [["/dashboard", "⌂", "Dashboard"], ["/shipments", "▣", "Shipments"], ["/vehicles", "▤", "Vehicles"], ["/maintenance", "⚙", "Maintenance"], ["/trips", "⌁", "Trips"], ["/live-tracking", "⌖", "Live Tracking"], ["/drivers", "♙", "Drivers"]],
  FleetManager: [["/dashboard", "⌂", "Dashboard"], ["/shipments", "▣", "Shipments"], ["/vehicles", "▤", "Vehicles"], ["/maintenance", "⚙", "Maintenance"], ["/trips", "⌁", "Trips"], ["/live-tracking", "⌖", "Live Tracking"], ["/drivers", "♙", "Drivers"]],
  Dispatcher: [["/dashboard", "⌂", "Dashboard"], ["/shipments", "▣", "Shipments"], ["/vehicles", "▤", "Vehicles"], ["/maintenance", "⚙", "Maintenance (Read Only)"], ["/trips", "⌁", "Trips"], ["/live-tracking", "⌖", "Live Tracking"], ["/drivers", "♙", "Drivers"]],
  Driver: [["/dashboard", "⌂", "Dashboard"], ["/shipments", "▣", "My Shipments"], ["/trips", "⌁", "My Trips"], ["/live-tracking", "⌖", "Live Tracking"], ["/drivers", "♙", "My Driver Profile"], ["/maintenance", "⚙", "My Vehicle Maintenance"], ["/fuel-log", "⛽", "My Fuel"]],
};

function Sidebar() {
  const { logout, user } = useContext(AuthContext);
  const navigate = useNavigate();
  const signOut = () => { logout(); navigate("/login", { replace: true }); };
  const navigation = navigationByRole[user?.role] || [["/dashboard", "⌂", "Dashboard"]];
  const analyticsNavigation = [
    ...(["Admin", "FleetManager"].includes(user?.role) ? [["/analytics/fleet", "◔", "Fleet Analytics"]] : []),
    ...(["Admin", "FleetManager", "Dispatcher"].includes(user?.role) ? [["/analytics/logistics", "◫", "Logistics Analytics"]] : []),
    ...(user?.role === "Admin" ? [["/analytics/admin", "◈", "Admin Analytics"]] : []),
  ];
  const fuelNavigation = ["Admin", "FleetManager", "Dispatcher"].includes(user?.role) ? [["/fuel-log", "⛽", user?.role === "Dispatcher" ? "Fuel Log (Read Only)" : "Fuel Log"]] : [];
  const reportsNavigation = ["Admin", "FleetManager", "Dispatcher"].includes(user?.role) ? [["/reports", "▤", "Reports"]] : [];
  return <aside className="app-sidebar"><NavLink className="sidebar-brand" to="/dashboard"><span>FF</span><strong>FleetFlow</strong></NavLink><p>Workspace</p><nav>{navigation.map(([path, icon, label]) => <NavLink key={path} to={path}>{icon}<span>{label}</span></NavLink>)}{fuelNavigation.map(([path, icon, label]) => <NavLink key={path} to={path}>{icon}<span>{label}</span></NavLink>)}{reportsNavigation.map(([path, icon, label]) => <NavLink key={path} to={path}>{icon}<span>{label}</span></NavLink>)}{analyticsNavigation.map(([path, icon, label]) => <NavLink key={path} to={path}>{icon}<span>{label}</span></NavLink>)}</nav><p>Account</p><nav><NavLink to="/profile">◉<span>Profile</span></NavLink></nav><div className="sidebar-footer"><button onClick={signOut}>⇥<span>Logout</span></button><button onClick={signOut} className="sidebar-signout">Sign Out</button></div></aside>;
}

export default Sidebar;
