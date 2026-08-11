# defMONV - patch defMON for Vessel MIDI clock, assemble, exomize, build a d64.
#
#   make            build defmonv.d64 (the release artifact)
#   make verify     assemble + assert the patch sites (no emulator)
#   make test       run the asid-vice integration test (needs Docker + driver)
#   make clean
#
# Tools: java + Kick Assembler (KICKASS_JAR), exomizer, python3, and a
# container runtime for c1541. Set C1541 to use a host VICE install instead.

KICKASS_JAR ?= vendor/KickAss.jar
JAVA        ?= java
EXOMIZER    ?= exomizer
PYTHON      ?= python3

VICE_IMAGE ?= anarkiwi/asid-vice:3.10.0.0
# HOME must be writable by the calling uid or VICE logs errors creating its
# config, cache and state directories.
C1541      ?= docker run --rm -u $(shell id -u):$(shell id -g) \
    -v $(CURDIR):/work -w /work -e HOME=/tmp --entrypoint c1541 $(VICE_IMAGE)

NAME    = defmonv
ENTRY   = 0x0800   # defMON cold-start (static-image entry)

PATCHED = build/$(NAME)-patched.asm
STATIC  = build/$(NAME)-static.prg
PACKED  = build/$(NAME).prg

all: $(NAME).d64

$(PATCHED): vendor/defmon.asm tools/patch_vessel.py
	mkdir -p build
	$(PYTHON) tools/patch_vessel.py vendor/defmon.asm $@

$(STATIC): $(PATCHED)
	$(JAVA) -jar $(KICKASS_JAR) $(PATCHED) -o $@

verify: $(STATIC)
	$(PYTHON) tools/verify_image.py $(STATIC)

$(PACKED): $(STATIC) verify
	$(EXOMIZER) sfx $(ENTRY) -o $@ $(STATIC)

$(NAME).d64: $(PACKED)
	rm -f $@
	$(C1541) -format "$(NAME),dv" d64 $@ -write $(PACKED) $(NAME)

test: $(NAME).d64
	$(PYTHON) tests/integration_test.py $(NAME).d64

clean:
	rm -rf build $(NAME).d64

.PHONY: all verify test clean
