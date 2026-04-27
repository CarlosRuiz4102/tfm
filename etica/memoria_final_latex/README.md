# Memoria ética del TFM

Archivos principales:

- `main.tex`: memoria en formato LaTeX tipo arXiv.
- `references.bib`: bibliografía.
- `PRIMEarxiv.sty`: estilo local mínimo para que el proyecto compile sin depender de archivos externos de la plantilla.

Compilación recomendada en Overleaf:

1. Subir los tres archivos de esta carpeta.
2. Seleccionar `main.tex` como archivo principal.
3. Compilar con pdfLaTeX.

Compilación local, si hay distribución TeX instalada:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

El documento ya incluye el autor Carlos Ruiz Oyarzun y el correo c.ruizoyarzun@alumnos.upm.es.
