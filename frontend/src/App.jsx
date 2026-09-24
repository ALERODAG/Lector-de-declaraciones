import { useState, useMemo } from 'react';
import * as XLSX from 'xlsx';
import {
  Download, Loader2, CheckCircle2, FileText, Receipt, Package, FileSpreadsheet, BarChart3
} from 'lucide-react';
import './App.css';

// Components
import { DataTable } from './components/DataTable';
import { InvoiceView } from './components/InvoiceView';
import { ProductModal } from './components/ProductModal';
import { Sidebar, Header } from './components/Layout';
import { UploadZone } from './components/UploadZone';
import { Comparative } from './components/Comparative';

// Services
import { api } from './services/api';

/* ══════════════════════════════════════════════════════════════════════
   Main App
   ══════════════════════════════════════════════════════════════════════ */

export default function App() {
  const [declFile, setDeclFile] = useState(null);
  const [invoiceFiles, setInvoiceFiles] = useState([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState('products');
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [observations, setObservations] = useState({});
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleDeclChange = (e) => {
    const f = e.target.files[0];
    if (f && f.name.toLowerCase().endsWith('.pdf')) {
      setDeclFile(f);
      setError(null);
    } else {
      setError('Por favor sube un archivo PDF válido para la declaración.');
    }
  };

  const handleInvoiceChange = (e) => {
    const files = Array.from(e.target.files);
    const validFiles = files.filter(f => f.name.toLowerCase().endsWith('.pdf'));
    setInvoiceFiles(prev => [...prev, ...validFiles]);
  };

  const removeInvoice = (index) => {
    setInvoiceFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleProcess = async () => {
    if (!declFile) {
      setError("Debes subir al menos la declaración de importación.");
      return;
    }
    setLoading(true); 
    setError(null);
    try {
      const data = await api.processFiles(declFile, invoiceFiles);
      setResult(data);
      if (data.invoices && data.invoices.length > 0) {
        setActiveTab('invoice');
      } else {
        setActiveTab('products');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const saveObservation = (product, text) => {
    const key = product.Referencia || product.Producto || JSON.stringify(product);
    setObservations(prev => ({ ...prev, [key]: text }));
  };

  const handleExport = () => {
    if (!result) return;
    const wb = XLSX.utils.book_new();
    if (result.declarations && result.declarations.length > 0) {
      const ws1 = XLSX.utils.json_to_sheet(result.declarations);
      XLSX.utils.book_append_sheet(wb, ws1, 'Declaraciones');
    }
    if (result.products && result.products.length > 0) {
      const ws2 = XLSX.utils.json_to_sheet(result.products);
      XLSX.utils.book_append_sheet(wb, ws2, 'Productos');
    }
    XLSX.writeFile(wb, `resultado_${declFile?.name || 'datos'}.xlsx`);
  };

  const declarations = result?.declarations ?? [];
  const products = result?.products ?? [];

  const totalQuantity = useMemo(() => {
    return products.reduce((acc, p) => {
      const val = p.Cantidad || p.CANTIDAD || 0;
      const num = typeof val === 'string'
        ? parseFloat(val.replace(/\./g, '').replace(',', '.'))
        : parseFloat(val);
      return acc + (isNaN(num) ? 0 : num);
    }, 0);
  }, [products]);

  return (
    <div className="app-layout">
      <Sidebar 
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        declarationsCount={declarations.length}
        productsCount={products.length}
        invoicesCount={result?.invoices?.length || 0}
      />

      <div className="main-area">
        <Header setSidebarOpen={setSidebarOpen} />

        <main className="content">
          {!result && !loading && (
            <UploadZone 
              declFile={declFile}
              handleDeclChange={handleDeclChange}
              invoiceFiles={invoiceFiles}
              handleInvoiceChange={handleInvoiceChange}
              removeInvoice={removeInvoice}
              handleProcess={handleProcess}
              loading={loading}
              error={error}
            />
          )}

          {loading && (
            <div className="loader-wrap">
              <Loader2 className="spinner" size={48} />
              <p>Procesando documentos y extrayendo información...</p>
            </div>
          )}

          {result && !loading && (
            <div className="results-view">
              <div className="results-header">
                <div>
                  <h1 className="page-title">Resultados del análisis</h1>
                  <p className="page-subtitle">{declFile?.name} + {invoiceFiles.length} facturas</p>
                </div>
                <div className="alert alert-success compact">
                  <CheckCircle2 size={16} /> Procesado correctamente
                </div>
              </div>

              {/* Stats Row */}
              <div className="stats-row">
                <StatCard icon={<FileText size={24} />} value={declarations.length} label="Declaraciones" />
                <StatCard icon={<Receipt size={24} />} value={totalQuantity.toLocaleString()} label="Cantidad Total" />
                <StatCard icon={<Package size={24} />} value={result.invoices.length} label="Facturas" />
                <StatCard icon={<FileSpreadsheet size={24} />} value={products.length} label="Productos DIM" />
              </div>

              {/* Tabs */}
              <div className="tabs-container">
                <TabButton 
                  active={activeTab === 'declarations'} 
                  onClick={() => setActiveTab('declarations')}
                  icon={<FileSpreadsheet size={18} />}
                  label="Declaraciones"
                />
                <TabButton 
                  active={activeTab === 'products'} 
                  onClick={() => setActiveTab('products')}
                  icon={<Package size={18} />}
                  label="Productos DIM"
                />
                <TabButton 
                  active={activeTab === 'invoice'} 
                  onClick={() => setActiveTab('invoice')}
                  icon={<Receipt size={18} />}
                  label="Facturas Extraídas"
                />
                <TabButton 
                  active={activeTab === 'comparative'} 
                  onClick={() => setActiveTab('comparative')}
                  icon={<BarChart3 size={18} />}
                  label="Comparativo"
                />
              </div>

              {/* Tab Content */}
              <div className="tab-content">
                {activeTab === 'declarations' && (
                  <DataTable data={declarations} title="Declaraciones de Importación" />
                )}
                {activeTab === 'products' && (
                  <DataTable
                    data={products}
                    title="Productos de la Declaración"
                    onRowClick={setSelectedProduct}
                  />
                )}
                {activeTab === 'invoice' && (
                  <div className="invoice-tab-content">
                    <input
                      id="tab-inv-input"
                      type="file"
                      accept=".pdf"
                      multiple
                      hidden
                      onChange={handleInvoiceChange}
                    />
                    <InvoiceView
                      invoices={result.invoices}
                      onUpload={() => document.getElementById('tab-inv-input').click()}
                      allDeclarations={result.declarations}
                    />

                    {invoiceFiles.length > result.invoices.length && (
                      <div className="floating-action-bar">
                        <div className="file-info">
                          <strong>{invoiceFiles.length - result.invoices.length}</strong> factura(s) nueva(s) seleccionada(s)
                        </div>
                        <button className="btn btn-primary" onClick={handleProcess}>
                          <Loader2 size={16} className={loading ? 'spinner' : 'hidden'} />
                          Procesar y actualizar
                        </button>
                      </div>
                    )}
                  </div>
                )}
                {activeTab === 'comparative' && (
                  <Comparative
                    comparative={result.comparative}
                    onSaveObservation={(ref, text) =>
                      setObservations(prev => ({ ...prev, [`ref:${ref}`]: text }))
                    }
                    savedObservations={observations}
                  />
                )}
              </div>

              <div className="action-footer">
                <button className="btn btn-primary" onClick={() => window.location.reload()}>Subir nuevos archivos</button>
                <button className="btn btn-secondary" onClick={handleExport}>
                  <Download size={16} style={{ marginRight: 8 }} /> Exportar a Excel
                </button>
              </div>
            </div>
          )}
        </main>
      </div>

      {selectedProduct && (
        <ProductModal
          product={selectedProduct}
          onClose={() => setSelectedProduct(null)}
          onSaveObservation={saveObservation}
          savedObservation={observations[selectedProduct.Referencia || selectedProduct.Producto || JSON.stringify(selectedProduct)]}
        />
      )}
    </div>
  );
}

function StatCard({ icon, value, label }) {
  return (
    <div className="stat-card">
      <div className="stat-icon">{icon}</div>
      <div className="stat-content">
        <span className="stat-value">{value}</span>
        <span className="stat-label">{label}</span>
      </div>
    </div>
  );
}

function TabButton({ active, onClick, icon, label }) {
  return (
    <button className={`tab-btn ${active ? 'active' : ''}`} onClick={onClick}>
      {icon} {label}
    </button>
  );
}
