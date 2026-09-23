import { FileSpreadsheet, Receipt, X, Loader2 } from 'lucide-react';

export function UploadZone({ 
  declFile, 
  handleDeclChange, 
  invoiceFiles, 
  handleInvoiceChange, 
  removeInvoice, 
  handleProcess, 
  loading, 
  error 
}) {
  return (
    <div className="upload-container-grid">
      {/* Declaración */}
      <div className="upload-section">
        <div className="upload-zone" onClick={() => document.getElementById('decl-input').click()}>
          <FileSpreadsheet size={40} className="upload-icon-decl" />
          <h4>{declFile ? declFile.name : 'Subir Declaración'}</h4>
          <p>Documento DIM principal (PDF)</p>
          <input id="decl-input" type="file" accept=".pdf" hidden onChange={handleDeclChange} />
        </div>
      </div>

      {/* Facturas */}
      <div className="upload-section">
        <div className="upload-zone secondary" onClick={() => document.getElementById('inv-input').click()}>
          <Receipt size={40} className="upload-icon-inv" />
          <h4>Sube tus facturas</h4>
          <p>Uno o más archivos (PDF)</p>
          <input id="inv-input" type="file" accept=".pdf" multiple hidden onChange={handleInvoiceChange} />
        </div>

        {invoiceFiles.length > 0 && (
          <div className="file-list">
            {invoiceFiles.map((f, i) => (
              <div key={i} className="file-item">
                <span title={f.name}>{f.name}</span>
                <button className="remove-file-btn" onClick={(e) => { e.stopPropagation(); removeInvoice(i); }}>
                  <X size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="process-button-container">
        <button className="btn btn-primary btn-lg" onClick={handleProcess} disabled={!declFile || loading}>
          {loading ? <Loader2 size={20} className="spinner" /> : null}
          <span style={{ marginLeft: loading ? 8 : 0 }}>
            {loading ? 'Procesando...' : 'Procesar todos los archivos'}
          </span>
        </button>
        {error && <div className="alert alert-error mt-20">{error}</div>}
      </div>
    </div>
  );
}
