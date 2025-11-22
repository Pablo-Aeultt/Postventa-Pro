# Carpeta de Imágenes y Videos Estáticos

## Logo de la Plataforma

Coloca aquí tu logo con el nombre **`logo`** y la extensión correspondiente.

### Formatos soportados (en orden de prioridad):

#### Videos (recomendado para logos animados):
- **logo.mp4** - MP4 (más compatible)
- **logo.webm** - WebM (mejor compresión)
- **logo.mov** - MOV (QuickTime)

#### Imágenes:
- **logo.svg** - SVG (vectorial, ideal para logos)
- **logo.png** - PNG (con transparencia)
- **logo.jpg** - JPG (sin transparencia)
- **logo.gif** - GIF (animado)

### Especificaciones recomendadas:

**Para videos:**
- **Duración**: 2-5 segundos (se reproducirá en loop)
- **Resolución**: 400x400 px o 500x500 px (cuadrado)
- **Peso**: Menos de 2 MB
- **Sin audio**: El video se reproduce muted
- **Configuración**: autoplay, loop, muted

**Para imágenes:**
- **Formato**: PNG (con fondo transparente) o SVG
- **Tamaño**: 400x400 px (cuadrado)
- **Peso**: Menos de 500 KB
- **Relación de aspecto**: 1:1 (cuadrado)

### Funcionamiento:
El sistema buscará automáticamente en este orden:
1. logo.mp4
2. logo.webm
3. logo.mov
4. logo.svg
5. logo.png
6. logo.jpg
7. logo.gif

Si no encuentra ningún archivo, mostrará el texto "PostVenta".

### El logo se mostrará en:
- Formulario de creación de reclamos
- Otras páginas de la plataforma (futuro)

### Recomendación:
Para un logo animado profesional, usa **MP4** con fondo transparente (alpha channel).
