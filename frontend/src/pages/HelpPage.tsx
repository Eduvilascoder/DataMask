import React from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  ExpandableSection,
  Box,
  Table,
} from '@cloudscape-design/components';

const HelpPage: React.FC = () => {
  return (
    <SpaceBetween size="l">
      <Container
        header={
          <Header variant="h1" description="Guía de uso y referencia de DataMask">
            Ayuda
          </Header>
        }
      >
        <SpaceBetween size="l">
          <ExpandableSection
            headerText="Cómo usar DataMask"
            defaultExpanded
          >
            <SpaceBetween size="s">
              <Box variant="p">
                Siga estos pasos para procesar sus documentos:
              </Box>
              <Box variant="p">
                <strong>1.</strong> Vaya a la sección "Procesamiento" en el menú lateral.
              </Box>
              <Box variant="p">
                <strong>2.</strong> Ingrese la ruta de la carpeta que contiene los documentos a procesar, o use el botón "Explorar" para navegar el sistema de archivos.
              </Box>
              <Box variant="p">
                <strong>3.</strong> Haga clic en "Validar carpeta" para listar los documentos encontrados.
              </Box>
              <Box variant="p">
                <strong>4.</strong> Seleccione los archivos que desea procesar (o procese todos).
              </Box>
              <Box variant="p">
                <strong>5.</strong> Haga clic en "Iniciar procesamiento". El progreso se mostrará en tiempo real.
              </Box>
              <Box variant="p">
                <strong>6.</strong> Los archivos ofuscados se guardarán en la carpeta <code>ofuscados/</code> y las versiones Markdown en <code>ofuscados_md/</code>.
              </Box>
              <Box variant="p">
                <strong>7.</strong> Revise los resultados en la sección "Archivos ofuscados" y el historial en "Registros de Auditoría".
              </Box>
              <Box variant="h4">Iniciar y detener la aplicación</Box>
              <Box variant="p">
                <strong>Iniciar:</strong> Ejecute <code>./run.sh</code> (macOS) o <code>run.bat</code> (Windows) desde el directorio del proyecto.
              </Box>
              <Box variant="p">
                <strong>Detener:</strong> Ejecute <code>./stop.sh</code> (macOS) o <code>stop.bat</code> (Windows), o presione <code>Ctrl+C</code> en la terminal donde se ejecuta el servidor.
              </Box>
            </SpaceBetween>
          </ExpandableSection>

          <ExpandableSection headerText="Formatos soportados">
            <Table
              columnDefinitions={[
                {
                  id: 'format',
                  header: 'Formato',
                  cell: (item) => <strong>{item.format}</strong>,
                },
                {
                  id: 'extension',
                  header: 'Extensión',
                  cell: (item) => <code>{item.extension}</code>,
                },
                {
                  id: 'description',
                  header: 'Descripción',
                  cell: (item) => item.description,
                },
              ]}
              items={[
                {
                  format: 'PDF',
                  extension: '.pdf',
                  description: 'Documentos PDF. Se aplican redacciones visuales preservando el formato original.',
                },
                {
                  format: 'Markdown',
                  extension: '.md',
                  description: 'Archivos de texto con formato Markdown. Se reemplazan los datos sensibles con etiquetas.',
                },
                {
                  format: 'Microsoft Word',
                  extension: '.docx',
                  description: 'Documentos Word (formato Open XML). Se reemplazan los datos sensibles en los párrafos.',
                },
              ]}
              variant="embedded"
              stripedRows
            />
          </ExpandableSection>

          <ExpandableSection headerText="Tipos de datos detectados">
            <Table
              columnDefinitions={[
                {
                  id: 'type',
                  header: 'Tipo',
                  cell: (item) => <strong>{item.type}</strong>,
                },
                {
                  id: 'label',
                  header: 'Etiqueta',
                  cell: (item) => <code>[{item.label}]</code>,
                },
                {
                  id: 'example',
                  header: 'Ejemplo',
                  cell: (item) => item.example,
                },
              ]}
              items={[
                { type: 'Nombre y Apellido', label: 'NOMBRE', example: 'Juan Pérez, María García López' },
                { type: 'Correo Electrónico', label: 'EMAIL', example: 'usuario@ejemplo.com' },
                { type: 'Celular', label: 'CELULAR', example: '+54 9 11 1234-5678' },
                { type: 'Teléfono', label: 'TELEFONO', example: '+54 11 4567-8901' },
                { type: 'Dirección', label: 'DIRECCION', example: 'Av. Corrientes 1234, CABA' },
                { type: 'Tarjeta de Crédito', label: 'TARJETA_CREDITO', example: '4532 1234 5678 9012' },
                { type: 'Cuenta Bancaria (CBU)', label: 'CUENTA_BANCARIA', example: '0110012230001234567890' },
                { type: 'DNI', label: 'DNI', example: '32.456.789 o 32456789' },
                { type: 'CUIT/CUIL', label: 'CUIT_CUIL', example: '20-32456789-4' },
                { type: 'Pasaporte', label: 'PASAPORTE', example: 'AAB123456' },
              ]}
              variant="embedded"
              stripedRows
            />
          </ExpandableSection>

          <ExpandableSection headerText="Restricciones y limitaciones">
            <SpaceBetween size="s">
              <Box variant="p">
                • El procesamiento es 100% local, no se envían datos a internet.
              </Box>
              <Box variant="p">
                • Los archivos Word (.docx) protegidos con contraseña no pueden procesarse.
              </Box>
              <Box variant="p">
                • Los PDFs protegidos con contraseña se omiten.
              </Box>
              <Box variant="p">
                • El modelo NER puede no detectar todos los datos sensibles (precisión ~85-95%).
              </Box>
              <Box variant="p">
                • Archivos muy grandes (&gt;50MB) pueden tardar varios minutos.
              </Box>
              <Box variant="p">
                • Se requiere ~2GB de espacio en disco para el modelo de IA.
              </Box>
              <Box variant="p">
                • Solo se procesan archivos en el nivel superior de la carpeta (no subcarpetas).
              </Box>
            </SpaceBetween>
          </ExpandableSection>

          <ExpandableSection headerText="Seguridad y riesgos">
            <SpaceBetween size="s">
              <Box variant="p">
                <strong>Modelo de seguridad:</strong> DataMask está diseñado para ejecutarse exclusivamente en localhost (127.0.0.1). No es accesible desde otros dispositivos en la red.
              </Box>
              <Box variant="h4">Riesgos conocidos</Box>
              <Box variant="p">
                • <strong>Acceso al sistema de archivos:</strong> La aplicación puede navegar y procesar archivos de cualquier ubicación del disco local. No restringe el acceso a directorios específicos. Esto es por diseño para flexibilidad, pero significa que cualquier persona con acceso al navegador en la máquina puede explorar el filesystem.
              </Box>
              <Box variant="p">
                • <strong>Sin autenticación:</strong> No se requiere usuario ni contraseña para acceder a la aplicación. Si alguien tiene acceso físico o remoto a su máquina, puede usar DataMask sin restricciones.
              </Box>
              <Box variant="p">
                • <strong>Logs con nombres de archivo:</strong> El registro de auditoría almacena los nombres completos de los archivos procesados. Si los nombres contienen información sensible (ej: "CV-Juan-Perez.pdf"), esta información queda registrada en el log.
              </Box>
              <Box variant="p">
                • <strong>Archivos ofuscados retienen contenido parcial:</strong> Los documentos ofuscados aún contienen la mayor parte del texto original — solo los datos sensibles detectados son reemplazados. El modelo NER tiene una precisión del 85-95%, por lo que algunos datos podrían no ser detectados.
              </Box>
              <Box variant="p">
                • <strong>Patrones regex personalizados:</strong> Si agrega patrones regex complejos en la configuración, un patrón mal formado podría causar lentitud en el procesamiento (ReDoS).
              </Box>
              <Box variant="h4">Mitigaciones implementadas</Box>
              <Box variant="p">
                • El servidor solo escucha en 127.0.0.1 (no accesible desde la red).
              </Box>
              <Box variant="p">
                • Los endpoints de borrado validan que los archivos estén dentro de las carpetas permitidas (protección contra path traversal).
              </Box>
              <Box variant="p">
                • No se realizan conexiones a internet durante el procesamiento.
              </Box>
              <Box variant="p">
                • Los archivos originales nunca se modifican.
              </Box>
              <Box variant="h4">Recomendaciones</Box>
              <Box variant="p">
                • No deje la aplicación corriendo cuando no la esté usando.
              </Box>
              <Box variant="p">
                • Revise los archivos ofuscados antes de compartirlos para verificar que todos los datos sensibles fueron detectados.
              </Box>
              <Box variant="p">
                • Borre los archivos ofuscados y logs cuando ya no los necesite (use la sección "Archivos ofuscados").
              </Box>
              <Box variant="p">
                • Si necesita exponer la aplicación a la red, configure autenticación adicional a nivel de red (VPN, firewall).
              </Box>
            </SpaceBetween>
          </ExpandableSection>

          <ExpandableSection headerText="Acerca de">
            <SpaceBetween size="s">
              <Box variant="p">
                <strong>DataMask v3.2</strong>
              </Box>
              <Box variant="p">
                Herramienta de enmascaramiento de datos sensibles en documentos.
                Utiliza procesamiento de lenguaje natural (NER) con spaCy para
                detectar y ofuscar información personal identificable (PII).
              </Box>
              <Box variant="p">
                Desarrollado por <strong>EduTheCoder</strong>.
              </Box>
            </SpaceBetween>
          </ExpandableSection>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
};

export default HelpPage;
