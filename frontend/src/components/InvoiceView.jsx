import { useState, useMemo } from 'react';
import { Receipt, Plus, FileText, ChevronDown, BarChart3, Info, LayoutDashboard, Package } from 'lucide-react';
import { DataTable } from './DataTable';

const parseNumber = (value) => {
  if (value === null || value === undefined || value === '') return NaN;
  if (typeof value === 'object') {
    if ('amount' in value) return parseNumber(value.amount);
    if ('value' in value) return parseNumber(value.value);
    return parseNumber(String(value));
  }
  if (typeof value === 'number') return value;
  const raw = String(value).trim();
  if (raw === '') return NaN;
  let normalized;
  if (raw.includes(',')) {
    normalized = raw.replace(/\./g, '').replace(',', '.');
  } else if (raw.split('.').length > 2) {
    normalized = raw.replace(/\./g, '');
  } else {
    normalized = raw;
  }
  const number = Number(normalized);
  return Number.isNaN(number) ? NaN : number;
};

const formatCurrency = (value, currency = '') => {
  const number = parseNumber(value);
  if (Number.isNaN(number)) return '-';
  return `${currency ? `${currency} ` : ''}${number.toLocaleString('es-CO', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
};

const normalizeInvoiceItem = (item, defaultCurrency = '') => ({
  referencia: item.referencia,
  descripcion: item.descripcion,
  cantidad: item.cantidad?.value ?? item.cantidad ?? '',
  unidad: item.unidad,
  valor_unitario: formatCurrency(item.valor_unitario, item.valor_unitario?.currency ?? defaultCurrency),
  valor_total: formatCurrency(item.valor_total, item.valor_total?.currency ?? defaultCurrency),
});

export function InvoiceView({ invoices, onUpload, allDeclarations }) {
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [declIdx, setDeclIdx] = useState(0);
  const [subIdx, setSubIdx] = useState(0);
  const safeIdx = Math.min(selectedIdx, Math.max((invoices?.length || 1) - 1, 0));

  const invoiceItems = useMemo(() => {
    const data = invoices?.[safeIdx];
    if (!data?.items) return [];
    return data.items.map((item) => normalizeInvoiceItem(item, data.metadata?.moneda));
  }, [invoices, safeIdx]);

  const relatedDeclarations = useMemo(() => {
    if (!allDeclarations) return [];
    const registro = invoices?.[safeIdx]?.metadata?.registro_declaracion;
    const filtered = allDeclarations.filter(d =>
      d.DECLARACION === registro ||
      (d.DECLARACION && registro && d.DECLARACION.includes(registro)) ||
      (registro && d.DECLARACION && registro.includes(d.DECLARACION))
    );
    return filtered.length > 0 ? filtered : allDeclarations;
  }, [allDeclarations, invoices, safeIdx]);

  const declaration = relatedDeclarations[declIdx] || relatedDeclarations[0] || {};

  const allSubpartidas = useMemo(() => {
    const subSet = new Set();
    if (declaration.SUBPARTIDA_ARANCELARIA) {
      const parts = String(declaration.SUBPARTIDA_ARANCELARIA).split(/[\s,;\n]+/).filter(Boolean);
      parts.forEach(p => subSet.add(p));
    }
    return [...subSet];
  }, [declaration.SUBPARTIDA_ARANCELARIA]);

  if (!invoices || invoices.length === 0) {
    return (
      <div className="empty-state">
        <Receipt size={48} color="var(--text-muted)" style={{ marginBottom: 16 }} />
        <p>No hay información de facturas disponible.</p>
        <button
          className="btn btn-secondary"
          style={{ marginTop: 16 }}
          onClick={() => onUpload?.()}
        >
          <Plus size={16} style={{ marginRight: 8 }} /> Subir facturas
        </button>
      </div>
    );
  }

  const data = invoices[safeIdx];
  const { metadata } = data;
  const currentSubpartida = allSubpartidas[subIdx] || declaration?.SUBPARTIDA_ARANCELARIA || '-';

  return (
    <div className="invoice-view">
      <div className="invoice-view-controls">
        {invoices.length > 1 ? (
          <div className="invoice-selector">
            <span>Ver Factura:</span>
            {invoices.map((inv, idx) => (
              <button
                key={idx}
                className={`selector-btn ${selectedIdx === idx ? 'active' : ''}`}
                onClick={() => setSelectedIdx(idx)}
              >
                {inv.metadata?.num_factura || `Factura ${idx + 1}`}
              </button>
            ))}
          </div>
        ) : <div />}

        <button className="btn btn-secondary btn-sm" onClick={() => onUpload?.()}>
          <Plus size={14} style={{ marginRight: 6 }} /> Agregar factura
        </button>
      </div>

      <div className="invoice-summary-grid">
        {/* General Info Card */}
        <div className="invoice-card">
          <div className="invoice-card-header">
            <div className="invoice-header-title">
              <div className="invoice-icon-box"><FileText size={20} /></div>
              <h3>Información general</h3>
            </div>
            
            {invoices.length > 1 && (
              <div className="card-nav-controls">
                <button 
                  className="nav-arrow-btn"
                  onClick={() => setSelectedIdx(prev => (prev > 0 ? prev - 1 : invoices.length - 1))}
                  title="Anterior factura"
                >
                  <ChevronDown size={14} style={{ transform: 'rotate(90deg)' }} />
                </button>
                <span className="nav-counter">
                  {selectedIdx + 1} / {invoices.length}
                </span>
                <button 
                  className="nav-arrow-btn"
                  onClick={() => setSelectedIdx(prev => (prev < invoices.length - 1 ? prev + 1 : 0))}
                  title="Siguiente factura"
                >
                  <ChevronDown size={14} style={{ transform: 'rotate(-90deg)' }} />
                </button>
              </div>
            )}
          </div>
          <div className="invoice-card-body">
            <div className="detail-row"><span>Número de factura</span><strong>{metadata.num_factura}</strong></div>
            <div className="detail-row"><span>Fecha de factura</span><strong>{metadata.fecha_factura}</strong></div>
            <div className="detail-row"><span>Proveedor / Exportador</span><strong>{metadata.proveedor}</strong></div>
            <div className="detail-row"><span>País de origen</span><strong>{metadata.pais_origen}</strong></div>
            <div className="detail-row"><span>Incoterm</span><strong>{metadata.incoterm}</strong></div>
            <div className="detail-row"><span>Moneda</span><strong>{metadata.moneda}</strong></div>
            <div className="detail-row"><span>Tipo de cambio</span><strong>{metadata.tipo_cambio}</strong></div>
          </div>
        </div>

        {/* DIM Info Card */}
        <div className="invoice-card">
          <div className="invoice-card-header">
            <div className="invoice-header-title">
              <div className="invoice-icon-box"><Package size={20} /></div>
              <h3>Información DIM</h3>
            </div>
            
            {relatedDeclarations.length > 1 && (
              <div className="card-nav-controls">
                <button 
                  className="nav-arrow-btn"
                  onClick={() => setDeclIdx(prev => (prev > 0 ? prev - 1 : relatedDeclarations.length - 1))}
                  title="Anterior declaración"
                >
                  <ChevronDown size={14} style={{ transform: 'rotate(90deg)' }} />
                </button>
                <span className="nav-counter">
                  {declIdx + 1} / {relatedDeclarations.length}
                </span>
                <button 
                  className="nav-arrow-btn"
                  onClick={() => setDeclIdx(prev => (prev < relatedDeclarations.length - 1 ? prev + 1 : 0))}
                  title="Siguiente declaración"
                >
                  <ChevronDown size={14} style={{ transform: 'rotate(-90deg)' }} />
                </button>
              </div>
            )}
          </div>
          <div className="invoice-card-body">
            <div className="detail-row"><span>Declaración</span><strong>{declaration?.DECLARACION || '-'}</strong></div>
            <div className="detail-row"><span>Importadores (NIT)</span><strong>{declaration?.NIT_DECLARANTE || '-'}</strong></div>
            <div className="detail-row"><span>Países de origen</span><strong>{declaration?.COD_PAIS_EXPORTADOR || '-'}</strong></div>
            <div className="detail-row"><span>Tipo de declaraciones</span><strong>{declaration?.TIPO_DECLARACION || '-'}</strong></div>
            <div className="detail-row">
              <span>Subpartida arancelaria</span>
              <div className="subpartida-controls">
                {allSubpartidas.length > 1 && (
                  <button 
                    className="nav-arrow-btn" 
                    onClick={() => setSubIdx(prev => (prev > 0 ? prev - 1 : allSubpartidas.length - 1))}
                    title="Anterior subpartida"
                  >
                    <ChevronDown size={14} style={{ transform: 'rotate(90deg)' }} />
                  </button>
                )}
                <strong className="subpartida-value">{currentSubpartida}</strong>
                {allSubpartidas.length > 1 && (
                  <button 
                    className="nav-arrow-btn" 
                    onClick={() => setSubIdx(prev => (prev < allSubpartidas.length - 1 ? prev + 1 : 0))}
                    title="Siguiente subpartida"
                  >
                    <ChevronDown size={14} style={{ transform: 'rotate(-90deg)' }} />
                  </button>
                )}
              </div>
            </div>
            <div className="detail-row"><span>Peso Bruto</span><strong>{declaration?.PESO_BRUTO || '-'}</strong></div>
            <div className="detail-row"><span>Valor FOB</span><strong>{declaration?.VALOR_FOB_USD || '-'}</strong></div>
          </div>
        </div>

        {/* Totals Card */}
        <div className="invoice-card totals-card">
          <div className="invoice-card-header">
            <div className="invoice-icon-box orange"><BarChart3 size={20} /></div>
            <h3>Totales factura</h3>
          </div>
          <div className="invoice-card-body">
            <div className="detail-row"><span>Total mercancía</span><strong>{formatCurrency(metadata.total_mercancia, metadata.moneda)}</strong></div>
            <div className="detail-row"><span>Flete internacional</span><strong>{formatCurrency(metadata.flete, metadata.moneda)}</strong></div>
            <div className="detail-row"><span>Seguro</span><strong>{formatCurrency(metadata.seguro, metadata.moneda)}</strong></div>
            <div className="detail-row"><span>Otros gastos</span><strong>{formatCurrency(metadata.otros_gastos, metadata.moneda)}</strong></div>

            <div className="total-main">
              <span>Total factura</span>
              <strong>{formatCurrency(metadata.total_factura, metadata.moneda)}</strong>
            </div>
          </div>
        </div>
      </div>

      <div className="tabs-container" style={{ marginTop: 32 }}>
        <button className="tab-btn active"><Package size={18} /> Detalle de productos</button>
        <button className="tab-btn"><BarChart3 size={18} /> Cargos y ajustes</button>
        <button className="tab-btn"><LayoutDashboard size={18} /> Totales por concepto</button>
      </div>

      <DataTable data={invoiceItems} title={`Productos Factura ${metadata.num_factura || (selectedIdx + 1)}`} />

      <div className="alert alert-info" style={{ marginTop: 24 }}>
        <Info size={16} /> Los valores mostrados están en {metadata.moneda}
      </div>
    </div>
  );
}
