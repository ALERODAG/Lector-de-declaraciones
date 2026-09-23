# Frontend — Lector de Declaraciones de Importación

Interfaz web del proyecto, construida con **React 19 + Vite**.

## Desarrollo

```powershell
npm install
npm run dev        # http://localhost:5173
```

La API FastAPI debe estar corriendo en `http://127.0.0.1:8000` (el proxy de Vite redirige `/api/v1`).

## Producción

```powershell
npm run build      # genera dist/ servido por FastAPI
```

El `dist/` es generado automáticamente en el Dockerfile multistage del proyecto.

## Componentes

- `UploadZone` — carga de declaración y facturas (multipart).
- `InvoiceView` — vista de la factura procesada: información general, totales, items y subpartidas relacionadas.
- `Comparative` — comparativo de datos entre documentos.
- `DataTable` — tabla genérica con búsqueda.
- `HelpModal` — guía de uso de la aplicación.

## Calidad

```powershell
npm run lint       # ESLint
npm run build      # build de producción
```