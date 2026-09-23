import { useState } from 'react';
import {
  X, LayoutDashboard, FileSpreadsheet, Package, Receipt, BarChart3, HelpCircle, ChevronDown
} from 'lucide-react';
import { HelpModal } from './HelpModal';

export function Sidebar({
  sidebarOpen,
  setSidebarOpen,
  activeTab,
  setActiveTab,
  declarationsCount,
  productsCount,
  invoicesCount
}) {
  const [helpOpen, setHelpOpen] = useState(false);

  return (
    <>
      {sidebarOpen && (
        <div className="modal-overlay sidebar-overlay" onClick={() => setSidebarOpen(false)} />
      )}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-nav">
          <div className="sidebar-header">
            <h2 className="sidebar-logo">DIM Reader</h2>
            <button className="mobile-close-btn" onClick={() => setSidebarOpen(false)}>
              <X size={20} />
            </button>
          </div>

          <button className="nav-item">
            <div className="nav-item-content"><LayoutDashboard size={20} /> Resumen</div>
          </button>

          <button
            className={`nav-item ${activeTab === 'declarations' ? 'active' : ''}`}
            onClick={() => { setActiveTab('declarations'); setSidebarOpen(false); }}
          >
            <div className="nav-item-content">
              <FileSpreadsheet size={20} /> Declaraciones
            </div>
            {declarationsCount > 0 && <span className="nav-badge">{declarationsCount}</span>}
          </button>

          <button
            className={`nav-item ${activeTab === 'products' ? 'active' : ''}`}
            onClick={() => { setActiveTab('products'); setSidebarOpen(false); }}
          >
            <div className="nav-item-content">
              <Package size={20} /> Productos
            </div>
            {productsCount > 0 && <span className="nav-badge">{productsCount}</span>}
          </button>

          <button
            className={`nav-item ${activeTab === 'invoice' ? 'active' : ''}`}
            onClick={() => { setActiveTab('invoice'); setSidebarOpen(false); }}
          >
            <div className="nav-item-content"><Receipt size={20} /> Factura</div>
            {invoicesCount > 0 && <span className="nav-badge">{invoicesCount}</span>}
          </button>

          <button className="nav-item">
            <div className="nav-item-content"><BarChart3 size={20} /> Comparativo</div>
          </button>
        </div>

        <div className="sidebar-footer">
          <button className="nav-item help-btn" onClick={() => setHelpOpen(true)}>
            <div className="nav-item-content"><HelpCircle size={20} /> Ayuda</div>
          </button>
          <div className="user-card">
            <div className="user-avatar">A</div>
            <div className="user-info">
              <div className="user-name">Administrador</div>
              <div className="user-email">alexi_rodriguez12@hotmail.com</div>
            </div>
            <ChevronDown size={14} className="user-chevron" />
          </div>
        </div>
      </aside>

      {helpOpen && <HelpModal onClose={() => setHelpOpen(false)} />}
    </>
  );
}

export function Header({ setSidebarOpen }) {
  return (
    <header className="header">
      <div className="header-brand">
        <button className="mobile-menu-btn" onClick={() => setSidebarOpen(true)}>
          <div className="menu-icon-container">☰</div>
        </button>
        <div className="header-logo">📋</div>
        <div>
          <div className="header-title">DIM Reader</div>
          <div className="header-subtitle">Gestión de Importaciones</div>
        </div>
      </div>
      <span className="header-badge">v1.0</span>
    </header>
  );
}
