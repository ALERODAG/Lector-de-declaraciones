import { useState } from 'react';
import { X, Save, AlertTriangle, CheckCircle2, BarChart3, FileText } from 'lucide-react';

/* ─────────────────────────────────────────────────────────────────────────
   Helpers
───────────────────────────────────────────────────────────────────────── */
const parseNum = (val) => {
  if (val === null || val === undefined || val === '') return 0;
  if (typeof val === 'object') {
    if ('amount' in val) return parseNum(val.amount);
    if ('value' in val) return parseNum(val.value);
    return parseNum(String(val));
  }
  if (typeof val === 'number') return val;
  return parseFloat(String(val).replace(/\./g, '').replace(',', '.')) || 0;
};

const fmtQty = (n) => {
  const num = parseNum(n);
  // No thousand separators — pure integer or up to 4 decimal places
  return Number.isInteger(num) ? String(num) : num.toFixed(4).replace(/\.?0+$/, '');
};

const fmtMoney = (n) =>
  `$ ${parseNum(n).toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const EPSILON_QTY   = 0.001;
const EPSILON_MONEY = 0.01;

/* ─────────────────────────────────────────────────────────────────────────
   Row processor — applies all business rules
───────────────────────────────────────────────────────────────────────── */
function processRow(row, idx) {
  const cantFact = parseNum(row.cantidad_factura ?? row.cantidad?.value ?? row.cantidad);
  const cantDim = parseNum(row.cantidad_dim ?? row.cantidad?.value ?? row.cantidad);
  let precioUnit = parseNum(row.precio_unitario_factura ?? row.valor_unitario?.amount ?? row.valor_unitario);
  let precioTotal = parseNum(row.precio_total_factura ?? row.valor_total?.amount ?? row.valor_total);

  if (!precioUnit && precioTotal && cantFact) {
    precioUnit = precioTotal / cantFact;
  }
  if (!precioTotal && precioUnit) {
    precioTotal = cantFact * precioUnit;
  }

  const coincidencia = cantDim * precioUnit;

  const cantMatch = Math.abs(cantFact - cantDim) < EPSILON_QTY;
  const moneyMatch = Math.abs(precioTotal - coincidencia) < EPSILON_MONEY;

  return {
    ...row,
    idx,
    cantidad_factura:         cantFact,
    cantidad_dim:             cantDim,
    precio_unitario_factura:  precioUnit,
    precio_total_factura:     precioTotal,
    coincidencia,
    cantMatch,
    moneyMatch,
    isValid: cantMatch && moneyMatch,
  };
}

/* ─────────────────────────────────────────────────────────────────────────
   Tiny styled badge
───────────────────────────────────────────────────────────────────────── */
function Badge({ value, ok }) {
  return (
    <span style={{
      display: 'inline-block',
      padding: '3px 10px',
      borderRadius: 6,
      fontWeight: 700,
      fontSize: 13,
      background: ok ? '#ECFDF5' : '#FEF2F2',
      color:      ok ? '#059669' : '#DC2626',
      border:     `1px solid ${ok ? '#A7F3D0' : '#FECACA'}`,
    }}>
      {value}
    </span>
  );
}

/* ─────────────────────────────────────────────────────────────────────────
   Field card used inside the modal
───────────────────────────────────────────────────────────────────────── */
function FieldCard({ label, value, isError, isOk }) {
  const bg     = isError ? '#FEF2F2' : isOk ? '#ECFDF5' : '#F9FAFB';
  const border = isError ? '#FECACA' : isOk ? '#A7F3D0' : '#E5E7EB';
  const color  = isError ? '#DC2626' : isOk ? '#059669' : 'var(--text-secondary)';
  return (
    <div style={{ background: bg, border: `1px solid ${border}`, borderRadius: 8, padding: '10px 14px' }}>
      <div style={{ fontSize: 11, color, fontWeight: 600, marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </div>
      <div style={{ fontSize: 14, fontWeight: 700, color }}>
        {value}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────
   Mini stat card for the header row
───────────────────────────────────────────────────────────────────────── */
function MiniStat({ icon, value, label, valueColor, iconBg, iconColor }) {
  return (
    <div className="stat-card" style={{ flex: 1, minWidth: 150, borderLeftColor: valueColor }}>
      <div className="stat-icon" style={{ background: iconBg, color: iconColor, border: 'none' }}>
        {icon}
      </div>
      <div className="stat-content">
        <span className="stat-value" style={{ color: valueColor, fontSize: 28 }}>{value}</span>
        <span className="stat-label">{label}</span>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────
   Row-detail Modal
───────────────────────────────────────────────────────────────────────── */
function DetailModal({ row, observation, onObsChange, onSave, onClose }) {
  const inconsistentFields = [];
  if (!row.cantMatch) {
    inconsistentFields.push(
      { label: 'Cantidad Factura', value: fmtQty(row.cantidad_factura) },
      { label: 'Cantidad DIM',     value: fmtQty(row.cantidad_dim) },
    );
  }
  if (!row.moneyMatch) {
    inconsistentFields.push(
      { label: 'Total Factura',   value: fmtMoney(row.precio_total_factura) },
      { label: 'Coincidencia DIM', value: fmtMoney(row.coincidencia) },
    );
  }

  return (
    <div
      className="modal-overlay"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="modal-content" style={{ maxWidth: 640 }}>
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title">
            {row.isValid
              ? <CheckCircle2 size={20} color="#059669" />
              : <AlertTriangle size={20} color="#F59E0B" />}
            {row.referencia || `Fila ${row.idx + 1}`}
          </div>
          <button className="btn btn-secondary" style={{ padding: '5px 10px' }} onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* Inconsistent fields */}
          {inconsistentFields.length > 0 && (
            <div>
              <p style={{ fontWeight: 700, color: '#DC2626', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
                <AlertTriangle size={15} /> Campos inconsistentes
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                {inconsistentFields.map((f, i) => (
                  <FieldCard key={i} label={f.label} value={f.value} isError />
                ))}
              </div>
            </div>
          )}

          {/* All fields */}
          <div>
            <p style={{ fontWeight: 700, marginBottom: 10, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 6 }}>
              <FileText size={15} /> Resumen completo
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <FieldCard label="Referencia"       value={row.referencia || '—'} />
              <FieldCard label="P. Unitario"      value={fmtMoney(row.precio_unitario_factura)} />
              <FieldCard
                label="Cant. Factura"
                value={fmtQty(row.cantidad_factura)}
                isError={!row.cantMatch}
                isOk={row.cantMatch}
              />
              <FieldCard
                label="Cant. DIM"
                value={fmtQty(row.cantidad_dim)}
                isError={!row.cantMatch}
                isOk={row.cantMatch}
              />
              <FieldCard
                label="Total Factura"
                value={fmtMoney(row.precio_total_factura)}
                isError={!row.moneyMatch}
                isOk={row.moneyMatch}
              />
              <FieldCard
                label="Coincidencia DIM"
                value={fmtMoney(row.coincidencia)}
                isError={!row.moneyMatch}
                isOk={row.moneyMatch}
              />
            </div>
          </div>

          {/* Observations */}
          <div className="observations-section" style={{ borderTop: '1px solid var(--border)', paddingTop: 16 }}>
            <label className="observations-label">Observaciones</label>
            <textarea
              className="observations-textarea"
              placeholder="Escribe una justificación o nota sobre esta fila..."
              value={observation}
              onChange={(e) => onObsChange(e.target.value)}
            />
          </div>
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Cerrar</button>
          <button
            className="btn btn-primary"
            onClick={onSave}
            disabled={!observation.trim()}
            style={{ opacity: !observation.trim() ? 0.5 : 1, display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <Save size={14} /> Guardar observación
          </button>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────
   Main Comparative Component
───────────────────────────────────────────────────────────────────────── */
export function Comparative({ rows = [], onSaveRow }) {
  const [modalRow,     setModalRow]     = useState(null);
  const [observations, setObservations] = useState({});
  const [savedRows,    setSavedRows]    = useState({});

  /* ── Empty state ───────────────────────────────────── */
  if (!rows || rows.length === 0) {
    return (
      <div className="empty-state">
        <BarChart3 size={40} style={{ marginBottom: 16, color: '#9CA3AF' }} />
        <p style={{ fontWeight: 600, marginBottom: 8 }}>Sin datos comparativos</p>
        <p style={{ fontSize: 13 }}>Procesa una declaración y facturas para ver el comparativo.</p>
      </div>
    );
  }

  /* ── Process rows ──────────────────────────────────── */
  const processed = rows.map((r, i) => processRow(r, i));

  const inconsistentCount = processed.filter(r => !r.isValid).length;
  const correctCount      = processed.length - inconsistentCount;

  /* ── Totals ────────────────────────────────────────── */
  const totals = processed.reduce(
    (acc, r) => ({
      cantFact:  acc.cantFact  + r.cantidad_factura,
      cantDim:   acc.cantDim   + r.cantidad_dim,
      total:     acc.total     + r.precio_total_factura,
      coinc:     acc.coinc     + r.coincidencia,
    }),
    { cantFact: 0, cantDim: 0, total: 0, coinc: 0 }
  );
  const totCantMatch  = Math.abs(totals.cantFact  - totals.cantDim) < EPSILON_QTY;
  const totMoneyMatch = Math.abs(totals.total      - totals.coinc)  < EPSILON_MONEY;

  /* ── Modal handlers ────────────────────────────────── */
  const handleSave = () => {
    if (!modalRow) return;
    const obs = observations[modalRow.idx] || '';
    if (onSaveRow) onSaveRow({ ...modalRow, observacion: obs });
    setSavedRows(prev => ({ ...prev, [modalRow.idx]: true }));
    setModalRow(null);
  };

  /* ─────────────────────────────────────────────────── */
  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', width: '100%' }}>

      {/* ── Header Stats ── */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 28, flexWrap: 'wrap' }}>
        <MiniStat
          icon={<BarChart3 size={22} />}
          value={rows.length}
          label="Total Productos"
          valueColor="var(--accent-dark)"
          iconBg="#FDFCF0"
          iconColor="var(--accent-dark)"
        />
        <MiniStat
          icon={<CheckCircle2 size={22} />}
          value={correctCount}
          label="Correctos"
          valueColor="#059669"
          iconBg="#ECFDF5"
          iconColor="#059669"
        />
        <MiniStat
          icon={<AlertTriangle size={22} />}
          value={inconsistentCount}
          label="Inconsistentes"
          valueColor={inconsistentCount === 0 ? '#059669' : '#DC2626'}
          iconBg={inconsistentCount === 0 ? '#ECFDF5' : '#FEF2F2'}
          iconColor={inconsistentCount === 0 ? '#059669' : '#DC2626'}
        />
      </div>

      {/* ── Table ── */}
      <div className="table-container">
        <div className="table-header-tools">
          <div>
            <span style={{ fontWeight: 700, fontSize: 16 }}>Comparativo DIM vs Facturas</span>
            <span style={{ fontSize: 13, color: 'var(--text-muted)', marginLeft: 12 }}>
              Haz clic en una fila para ver el detalle
            </span>
          </div>
          {inconsistentCount > 0 && (
            <span style={{
              background: '#FEF2F2',
              color: '#ee0c0c',
              border: '1px solid #FECACA',
              borderRadius: 20,
              padding: '4px 14px',
              fontSize: 12,
              fontWeight: 700,
            }}>
              ⚠ {inconsistentCount} fila(s) con error
            </span>
          )}
        </div>

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th style={{ width: 40 }}>#</th>
                <th>Referencia</th>
                <th style={{ textAlign: 'center' }}>Cant. Factura</th>
                <th style={{ textAlign: 'center' }}>Cant. DIM</th>
                <th style={{ textAlign: 'right' }}>P. Unit. Factura</th>
                <th style={{ textAlign: 'right' }}>Total Factura</th>
                <th style={{ textAlign: 'right' }}>Coincidencia</th>
                <th style={{ textAlign: 'center' }}>Estado</th>
              </tr>
            </thead>

            <tbody>
              {processed.map((row) => (
                <tr
                  key={row.idx}
                  onClick={() => setModalRow(row)}
                  style={{
                    cursor: 'pointer',
                    background: savedRows[row.idx] ? '#F0FDF4' : undefined,
                    transition: 'background 0.15s',
                  }}
                >
                  <td style={{ color: 'var(--text-muted)', fontWeight: 600, fontSize: 12 }}>
                    {row.idx + 1}
                  </td>
                  <td style={{ fontWeight: 600 }}>{row.referencia || '—'}</td>

                  {/* Cantidad Factura — green/red */}
                  <td style={{ textAlign: 'center' }}>
                    <Badge value={fmtQty(row.cantidad_factura)} ok={row.cantMatch} />
                  </td>

                  {/* Cantidad DIM — same color as above */}
                  <td style={{ textAlign: 'center' }}>
                    <Badge value={fmtQty(row.cantidad_dim)} ok={row.cantMatch} />
                  </td>

                  {/* Precio unitario — neutral */}
                  <td style={{ textAlign: 'right', color: 'var(--text-secondary)' }}>
                    {fmtMoney(row.precio_unitario_factura)}
                  </td>

                  {/* Total Factura — green/red */}
                  <td style={{ textAlign: 'right' }}>
                    <Badge value={fmtMoney(row.precio_total_factura)} ok={row.moneyMatch} />
                  </td>

                  {/* Coincidencia — same color as total */}
                  <td style={{ textAlign: 'right' }}>
                    <Badge value={fmtMoney(row.coincidencia)} ok={row.moneyMatch} />
                  </td>

                  {/* Estado */}
                  <td style={{ textAlign: 'center' }}>
                    {row.isValid
                      ? <span style={{ color: '#059669', fontWeight: 700, fontSize: 13 }}>✓ OK</span>
                      : <span style={{ color: '#DC2626', fontWeight: 700, fontSize: 13 }}>✗ Error</span>
                    }
                    {savedRows[row.idx] && (
                      <span style={{ fontSize: 11, color: '#059669', display: 'block' }}>guardado</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>

            {/* ── Totals row ── */}
            <tfoot>
              <tr style={{ background: '#F3F4F6' }}>
                <td colSpan={2} style={{ fontWeight: 800, fontSize: 13, color: 'var(--text-primary)' }}>
                  TOTALES
                </td>
                <td style={{ textAlign: 'center' }}>
                  <Badge value={fmtQty(totals.cantFact)} ok={totCantMatch} />
                </td>
                <td style={{ textAlign: 'center' }}>
                  <Badge value={fmtQty(totals.cantDim)} ok={totCantMatch} />
                </td>
                <td style={{ textAlign: 'right', color: 'var(--text-muted)', fontWeight: 600 }}>—</td>
                <td style={{ textAlign: 'right' }}>
                  <Badge value={fmtMoney(totals.total)} ok={totMoneyMatch} />
                </td>
                <td style={{ textAlign: 'right' }}>
                  <Badge value={fmtMoney(totals.coinc)} ok={totMoneyMatch} />
                </td>
                <td />
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* ── Detail Modal ── */}
      {modalRow && (
        <DetailModal
          row={modalRow}
          observation={observations[modalRow.idx] || ''}
          onObsChange={(val) => setObservations(prev => ({ ...prev, [modalRow.idx]: val }))}
          onSave={handleSave}
          onClose={() => setModalRow(null)}
        />
      )}
    </div>
  );
}
