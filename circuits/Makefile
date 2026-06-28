# Build all CircuiTikZ schematics in this directory to SVG.
#
#   make           - build every .tex into a sibling .svg
#   make foo.svg   - build a single circuit
#   make clean     - remove SVGs and build artefacts
#   make watch     - rebuild on save (needs entr)

# Every .tex EXCEPT header.tex and shared *_fig.tex fragments is a circuit.
# The *_fig.tex files hold one shared drawing that the thin _v / _i wrappers
# \input{} to emit the node-voltage (D2) and branch-current (D3) sheets.
FRAGMENTS := $(wildcard *_fig.tex)
CIRCUITS  := $(filter-out header.tex $(FRAGMENTS),$(wildcard *.tex))
SVGS      := $(CIRCUITS:.tex=.svg)

LATEX     ?= pdflatex
LATEXOPTS ?= -interaction=nonstopmode -halt-on-error -file-line-error

.PHONY: all clean watch
all: $(SVGS)

%.svg: %.tex header.tex $(FRAGMENTS)
	@mkdir -p build
	@echo "  LATEX  $<"
	@$(LATEX) $(LATEXOPTS) -output-directory=build $< > build/$*.compile.log 2>&1 \
	  || { echo "FAILED. Tail of log:"; tail -40 build/$*.compile.log; exit 1; }
	@echo "  SVG    $@"
	@pdftocairo -svg build/$*.pdf $@

clean:
	rm -rf build *.svg

watch:
	@command -v entr >/dev/null || { echo "install 'entr' for watch mode"; exit 1; }
	@ls *.tex header.tex | entr -c make
