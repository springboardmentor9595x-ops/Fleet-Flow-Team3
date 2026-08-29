import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";

function MainLayout({ children }) {
  return <div className="app-shell"><Sidebar /><section className="app-content"><Navbar /><main className="app-page">{children}</main></section></div>;
}

export default MainLayout;
