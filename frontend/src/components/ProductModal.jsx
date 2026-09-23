import { useState } from 'react';
import { Package, X } from 'lucide-react';

export function ProductModal({ product, onClose, onSaveObservation, savedObservation }) {
  const [observation, setObservation] = useState(savedObservation || '');

  if (!product) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <div className="modal-icon-container">
              <Package size={20} color="#000" />
            </div>
            Detalle del producto
          </div>
          <button onClick={onClose} className="close-modal-btn">
            <X size={24} />
          </button>
        </div>

        <div className="modal-body">
          <div className="product-details-grid">
            {Object.entries(product).map(([key, val]) => (
              <div key={key} className="detail-item">
                <span className="detail-label">{key.replace(/_/g, ' ')}</span>
                <span className="detail-value">{val || '-'}</span>
              </div>
            ))}
          </div>

          <div className="observations-section">
            <label className="observations-label">Observaciones</label>
            <textarea
              className="observations-textarea"
              placeholder="Ingrese observaciones sobre este producto..."
              value={observation}
              onChange={e => setObservation(e.target.value)}
              maxLength={500}
            />
            <div className="char-counter">
              {observation.length} / 500
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Cancelar</button>
          <button className="btn btn-primary" onClick={() => {
            onSaveObservation(product, observation);
            onClose();
          }}>
            Guardar observaciones
          </button>
        </div>
      </div>
    </div>
  );
}
