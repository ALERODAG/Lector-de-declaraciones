import { X, FileSpreadsheet, Receipt, Package, ChevronRight } from 'lucide-react';

const SECTIONS = [
  {
    id: 'inicio',
    emoji: '🚀',
    title: 'Cómo empezar',
    steps: [
      {
        step: 1,
        title: 'Sube tu Declaración de Importación (DIM)',
        desc: 'Haz clic en la zona "Subir Declaración" y selecciona el archivo PDF del documento DIM. Este archivo es obligatorio.',
        icon: <FileSpreadsheet size={20} />,
      },
      {
        step: 2,
        title: 'Adjunta las facturas (opcional)',
        desc: 'Puedes cargar una o varias facturas de proveedores en formato PDF. La aplicación identificará automáticamente el formato (Sofabex, ADK, Gate, u otros).',
        icon: <Receipt size={20} />,
      },
      {
        step: 3,
        title: 'Haz clic en "Procesar todos los archivos"',
        desc: 'El sistema extraerá toda la información automáticamente. El proceso puede tardar unos segundos dependiendo del tamaño de los PDFs.',
        icon: <Package size={20} />,
      },
    ],
  },
  {
    id: 'pestanas',
    emoji: '📑',
    title: 'Pestañas de resultados',
    items: [
      {
        icon: <FileSpreadsheet size={16} />,
        label: 'Declaraciones',
        desc: 'Datos generales del DIM: NIT, razón social, valores FOB, subpartidas arancelarias, país exportador, empresa transportadora, etc.',
      },
      {
        icon: <Package size={16} />,
        label: 'Productos DIM',
        desc: 'Listado detallado de productos: marca, modelo, referencia, cantidad, país de origen. Haz clic en cualquier fila para ver el detalle completo y agregar observaciones.',
      },
      {
        icon: <Receipt size={16} />,
        label: 'Facturas Extraídas',
        desc: 'Información de las facturas de proveedor: datos generales, ítems con precios, y cruce automático con la declaración DIM correspondiente.',
      },
    ],
  },
  {
    id: 'busqueda',
    emoji: '🔍',
    title: 'Búsqueda y filtros',
    content: 'Cada tabla tiene un campo de búsqueda en la parte superior. Escribe cualquier término (número de parte, país, valor, etc.) y la tabla se filtrará en tiempo real mostrando solo las filas que coincidan.',
  },
  {
    id: 'facturas',
    emoji: '📄',
    title: 'Agregar facturas después del proceso',
    content: 'En la pestaña "Facturas Extraídas" puedes hacer clic en "Agregar factura" para cargar PDFs adicionales. Cuando hayas seleccionado los nuevos archivos, una barra flotante en la parte inferior te permitirá procesarlos sin tener que subir la declaración nuevamente.',
  },
  {
    id: 'exportar',
    emoji: '📥',
    title: 'Exportar a Excel',
    content: 'Al finalizar el análisis, haz clic en el botón "Exportar a Excel" para descargar un archivo .xlsx con dos hojas: Declaraciones y Productos. El nombre del archivo incluirá el nombre del PDF procesado.',
  },
  {
    id: 'observaciones',
    emoji: '📝',
    title: 'Observaciones por producto',
    content: 'En la pestaña "Productos DIM", haz clic sobre cualquier fila de la tabla para abrir el panel de detalle del producto. Allí podrás escribir observaciones o notas. Estas observaciones se guardan durante la sesión actual.',
  },
  {
    id: 'nuevo',
    emoji: '🔄',
    title: 'Procesar nuevos archivos',
    content: 'Para analizar un nuevo conjunto de documentos, haz clic en "Subir nuevos archivos". Esto restablecerá la vista de carga y podrás comenzar de nuevo sin necesidad de recargar la página manualmente.',
  },
];

export function HelpModal({ onClose }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content help-modal"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="modal-header help-modal-header">
          <div className="modal-title">
            <div className="help-modal-icon">❓</div>
            Guía de uso — DIM Reader
          </div>
          <button className="close-modal-btn" onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        {/* Body */}
        <div className="modal-body help-modal-body">

          {/* Intro */}
          <div className="help-intro">
            <p>
              <strong>DIM Reader</strong> te permite extraer y visualizar la información contenida en Declaraciones
              de Importación (DIM) y facturas de proveedores en formato PDF, sin necesidad de copiar datos manualmente.
            </p>
          </div>

          {/* Sections */}
          {SECTIONS.map(section => (
            <div key={section.id} className="help-section">
              <h3 className="help-section-title">
                <span>{section.emoji}</span> {section.title}
              </h3>

              {/* Steps */}
              {section.steps && (
                <div className="help-steps">
                  {section.steps.map(s => (
                    <div key={s.step} className="help-step">
                      <div className="help-step-number">{s.step}</div>
                      <div className="help-step-body">
                        <div className="help-step-title">
                          <span className="help-step-icon">{s.icon}</span>
                          {s.title}
                        </div>
                        <p className="help-step-desc">{s.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Tab items */}
              {section.items && (
                <div className="help-tabs-list">
                  {section.items.map(item => (
                    <div key={item.label} className="help-tab-item">
                      <div className="help-tab-item-label">
                        <span className="help-tab-icon">{item.icon}</span>
                        <strong>{item.label}</strong>
                      </div>
                      <p>{item.desc}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Plain content */}
              {section.content && (
                <p className="help-section-content">{section.content}</p>
              )}
            </div>
          ))}

          {/* Tips */}
          <div className="help-tips">
            <h3 className="help-section-title"><span>💡</span> Consejos útiles</h3>
            <ul className="help-tips-list">
              <li><ChevronRight size={14} className="tip-arrow" /> Asegúrate de que el PDF tenga texto seleccionable (no sea una imagen escaneada).</li>
              <li><ChevronRight size={14} className="tip-arrow" /> Puedes cargar varias facturas al mismo tiempo manteniendo <kbd>Ctrl</kbd> al seleccionar archivos.</li>
              <li><ChevronRight size={14} className="tip-arrow" /> La búsqueda en las tablas filtra en todas las columnas simultáneamente.</li>
              <li><ChevronRight size={14} className="tip-arrow" /> Los botones de navegación <strong>‹ ›</strong> en las tarjetas de facturas permiten cambiar entre declaraciones relacionadas.</li>
            </ul>
          </div>

        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button className="btn btn-primary" onClick={onClose}>Entendido</button>
        </div>
      </div>
    </div>
  );
}
