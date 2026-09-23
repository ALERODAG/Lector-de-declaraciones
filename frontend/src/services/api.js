const API_BASE = '/api/v1';

export const api = {
  async processFiles(declFile, invoiceFiles) {
    const form = new FormData();
    form.append('declaration', declFile);
    invoiceFiles.forEach(f => {
      form.append('invoices', f);
    });

    const res = await fetch(`${API_BASE}/process-multiple`, {
      method: 'POST',
      body: form
    });
    
    if (!res.ok) {
      throw new Error(`Error del servidor: ${res.statusText}`);
    }

    const json = await res.json();
    if (!json.success) {
      throw new Error(json.message || 'Error desconocido al procesar archivos');
    }
    
    return json.data;
  }
};
