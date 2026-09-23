import { useState, useMemo } from 'react';
import { Search } from 'lucide-react';

export function DataTable({ data, title, onRowClick }) {
  const [search, setSearch] = useState('');

  const columns = useMemo(() => {
    if (!data || data.length === 0) return [];
    return Object.keys(data[0]);
  }, [data]);

  const filtered = useMemo(() => {
    if (!data) return [];
    return data.filter(row =>
      columns.some(col =>
        String(row[col] || '').toLowerCase().includes(search.toLowerCase())
      )
    );
  }, [data, search, columns]);

  if (!data || data.length === 0) {
    return (
      <div className="table-container">
        <div style={{ padding: 60, textAlign: 'center', color: 'var(--text-muted)' }}>
          No hay datos para mostrar en {title}
        </div>
      </div>
    );
  }

  return (
    <div className="table-container">
      <div className="table-header-tools">
        <div className="search-box">
          <Search size={18} className="search-icon" />
          <input
            placeholder={`Buscar en ${title.toLowerCase()}...`}
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          {filtered.length} / {data.length} filas
        </div>
      </div>

      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              {columns.map(col => (
                <th key={col}>{col.replace(/_/g, ' ')}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((row, i) => (
              <tr key={i} onClick={() => onRowClick?.(row)}>
                {columns.map(col => (
                  <td key={col} title={row[col]}>{row[col] || '—'}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="table-footer">
        <span>Mostrando {filtered.length} registros</span>
        <div className="pagination">
          <button className="page-btn active">1</button>
        </div>
      </div>
    </div>
  );
}
