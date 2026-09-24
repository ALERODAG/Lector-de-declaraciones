import { CheckCircle2, AlertTriangle, BarChart3, Scale } from 'lucide-react';

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
  return Number.isInteger(num) ? String(num) : num.toFixed(4).replace(/\.?0+$/, '');
};

const fmtMoney = (n) => {
  const num = parseNum(n);
  return `$${num.toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

const EPSILON_MONEY = 0.01;

/* ─────────────────────────────────────────────────────────────────────────
   Mini stat card
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
      whiteSpace: 'nowrap',
    }}>
      {value}
    </span>
  );
}

/* ─────────────────────────────────────────────────────────────────────────
   Section: Seguros (FOB × factor vs seguros declarado)
───────────────────────────────────────────────────────────────────────── */
function SegurosSection({ seguros = [], factorSeguros }) {
  const incorrectos = seguros.filter(s => !s.match).length;
  const correctos = seguros.length - incorrectos;

  return (
    <div className="table-container" style={{ marginBottom: 28 }}>
      <div className="table-header-tools">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Scale size={18} style={{ color: 'var(--accent-dark)' }} />
          <span style={{ fontWeight: 700, fontSize: 16 }}>Seguros USD — FOB × {parseNum(factorSeguros) * 100}%</span>
        </div>
        {incorrectos > 0 && (
          <span style={{
            background: '#FEF2F2', color: '#ee0c0c', border: '1px solid #FECACA',
            borderRadius: 20, padding: '4px 14px', fontSize: 12, fontWeight: 700,
          }}>
            ⚠ {incorrectos} declaración(es) con diferencia
          </span>
        )}
      </div>

      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Declaración</th>
              <th style={{ textAlign: 'right' }}>Valor FOB USD</th>
              <th style={{ textAlign: 'right' }}>Seguro Calculado</th>
              <th style={{ textAlign: 'right' }}>Seguro Declarado</th>
              <th style={{ textAlign: 'right' }}>Diferencia</th>
              <th style={{ textAlign: 'center' }}>Estado</th>
            </tr>
          </thead>
          <tbody>
            {seguros.map((s, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 600, fontSize: 13 }}>{s.declaracion}</td>
                <td style={{ textAlign: 'right', color: 'var(--text-secondary)' }}>{fmtMoney(s.fob_usd)}</td>
                <td style={{ textAlign: 'right' }}>
                  <Badge value={fmtMoney(s.seguros_calculado)} ok={s.match} />
                </td>
                <td style={{ textAlign: 'right' }}>
                  <Badge value={fmtMoney(s.seguros_declarado)} ok={s.match} />
                </td>
                <td style={{ textAlign: 'right', color: 'var(--text-secondary)' }}>
                  {parseNum(s.diferencia) === 0 ? '—' : fmtMoney(s.diferencia)}
                </td>
                <td style={{ textAlign: 'center' }}>
                  {s.match
                    ? <span style={{ color: '#059669', fontWeight: 700, fontSize: 13 }}>✓ Cuadra</span>
                    : <span style={{ color: '#DC2626', fontWeight: 700, fontSize: 13 }}>✗ No cuadra</span>}
                </td>
              </tr>
            ))}
          </tbody>
          {seguros.length > 0 && (
            <tfoot>
              <tr style={{ background: '#F3F4F6' }}>
                <td style={{ fontWeight: 800, fontSize: 13 }} colSpan={2}>TOTAL</td>
                <td style={{ textAlign: 'right' }}>
                  <Badge
                    value={fmtMoney(seguros.reduce((a, s) => a + parseNum(s.seguros_calculado), 0))}
                    ok={Math.abs(
                      seguros.reduce((a, s) => a + parseNum(s.seguros_calculado), 0) -
                      seguros.reduce((a, s) => a + parseNum(s.seguros_declarado), 0)
                    ) < EPSILON_MONEY}
                  />
                </td>
                <td style={{ textAlign: 'right' }}>
                  <Badge value={fmtMoney(seguros.reduce((a, s) => a + parseNum(s.seguros_declarado), 0))} ok />
                </td>
                <td style={{ textAlign: 'right', color: 'var(--text-muted)', fontWeight: 600 }}>—</td>
                <td />
              </tr>
            </tfoot>
          )}
        </table>
      </div>

      {seguros.length === 0 && (
        <p style={{ padding: '24px 16px', color: 'var(--text-muted)', fontSize: 13, textAlign: 'center' }}>
          No se encontraron valores FOB/seguros en la declaración.
        </p>
      )}

      {/* Resumen hidden — expuesto arriba para claridad */}
      <span style={{ display: 'none' }}>{correctos}</span>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────
   Section: Cantidades por referencia (DIM vs factura)
───────────────────────────────────────────────────────────────────────── */
function CantidadesSection({ cantidades = [] }) {
  const malas = cantidades.filter(c => !c.match).length;
  const buenas = cantidades.length - malas;

  return (
    <div className="table-container">
      <div className="table-header-tools">
        <div>
          <span style={{ fontWeight: 700, fontSize: 16 }}>Cantidades por Referencia — DIM vs Factura</span>
          <span style={{ fontSize: 13, color: 'var(--text-muted)', marginLeft: 12 }}>
            Referencias declaradas en la DIM presentes en la factura
          </span>
        </div>
        {malas > 0 && (
          <span style={{
            background: '#FEF2F2', color: '#ee0c0c', border: '1px solid #FECACA',
            borderRadius: 20, padding: '4px 14px', fontSize: 12, fontWeight: 700,
          }}>
            ⚠ {malas} referencia(s) con diferencia
          </span>
        )}
      </div>

      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Referencia</th>
              <th style={{ textAlign: 'center' }}>Cant. Factura</th>
              <th style={{ textAlign: 'center' }}>Cant. DIM</th>
              <th style={{ textAlign: 'center' }}>Estado</th>
            </tr>
          </thead>
          <tbody>
            {cantidades.map((c, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 600 }}>{c.referencia}</td>
                <td style={{ textAlign: 'center' }}>
                  <Badge value={fmtQty(c.cantidad_factura)} ok={c.match} />
                </td>
                <td style={{ textAlign: 'center' }}>
                  <Badge value={fmtQty(c.cantidad_dim)} ok={c.match} />
                </td>
                <td style={{ textAlign: 'center' }}>
                  {c.match
                    ? <span style={{ color: '#059669', fontWeight: 700, fontSize: 13 }}>✓ OK</span>
                    : <span style={{ color: '#DC2626', fontWeight: 700, fontSize: 13 }}>✗ Error</span>}
                </td>
              </tr>
            ))}
          </tbody>
          {cantidades.length > 0 && (
            <tfoot>
              <tr style={{ background: '#F3F4F6' }}>
                <td style={{ fontWeight: 800, fontSize: 13 }}>TOTAL</td>
                <td style={{ textAlign: 'center' }}>
                  <Badge
                    value={fmtQty(cantidades.reduce((a, c) => a + parseNum(c.cantidad_factura), 0))}
                    ok={Math.abs(
                      cantidades.reduce((a, c) => a + parseNum(c.cantidad_factura), 0) -
                      cantidades.reduce((a, c) => a + parseNum(c.cantidad_dim), 0)
                    ) < 1}
                  />
                </td>
                <td style={{ textAlign: 'center' }}>
                  <Badge value={fmtQty(cantidades.reduce((a, c) => a + parseNum(c.cantidad_dim), 0))} ok />
                </td>
                <td />
              </tr>
            </tfoot>
          )}
        </table>
      </div>

      {cantidades.length === 0 && (
        <p style={{ padding: '24px 16px', color: 'var(--text-muted)', fontSize: 13, textAlign: 'center' }}>
          No hay coincidencias entre las referencias de la DIM y la factura.
        </p>
      )}

      <span style={{ display: 'none' }}>{buenas}</span>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────
   Main Comparative Component
───────────────────────────────────────────────────────────────────────── */
export function Comparative({ comparative = {} }) {
  const seguros = comparative?.seguros ?? [];
  const cantidades = comparative?.cantidades ?? [];
  const factorSeguros = comparative?.factor_seguros;

  if (!seguros.length && !cantidades.length) {
    return (
      <div className="empty-state">
        <BarChart3 size={40} style={{ marginBottom: 16, color: '#9CA3AF' }} />
        <p style={{ fontWeight: 600, marginBottom: 8 }}>Sin datos comparativos</p>
        <p style={{ fontSize: 13 }}>Procesa una declaración con valores FOB y una factura para ver el comparativo.</p>
      </div>
    );
  }

  const segurosIncorrectos = seguros.filter(s => !s.match).length;
  const cantidadesIncorrectas = cantidades.filter(c => !c.match).length;

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', width: '100%' }}>
      <div style={{ display: 'flex', gap: 16, marginBottom: 28, flexWrap: 'wrap' }}>
        <MiniStat
          icon={<Scale size={22} />}
          value={seguros.length}
          label="Declaraciones (FOB)"
          valueColor="var(--accent-dark)"
          iconBg="#FDFCF0"
          iconColor="var(--accent-dark)"
        />
        <MiniStat
          icon={<CheckCircle2 size={22} />}
          value={seguros.length - segurosIncorrectos}
          label="Seguros que cuadran"
          valueColor="#059669"
          iconBg="#ECFDF5"
          iconColor="#059669"
        />
        <MiniStat
          icon={<AlertTriangle size={22} />}
          value={segurosIncorrectos}
          label="Seguros con diferencia"
          valueColor={segurosIncorrectos === 0 ? '#059669' : '#DC2626'}
          iconBg={segurosIncorrectos === 0 ? '#ECFDF5' : '#FEF2F2'}
          iconColor={segurosIncorrectos === 0 ? '#059669' : '#DC2626'}
        />
        <MiniStat
          icon={<BarChart3 size={22} />}
          value={cantidades.length}
          label="Referencias cruzadas"
          valueColor={cantidadesIncorrectas === 0 ? '#059669' : '#DC2626'}
          iconBg="#ECFDF5"
          iconColor="#059669"
        />
      </div>

      <SegurosSection seguros={seguros} factorSeguros={factorSeguros} />
      <CantidadesSection cantidades={cantidades} />
    </div>
  );
}