import os
import platform
import unittest
import re
import subprocess
from disassemble_reassemble_check import (
    compile,
    cd,
    disassemble,
    reassemble,
    test,
    make,
)
from pathlib import Path
from typing import Optional, Tuple
from gtirb.cfg import EdgeType
import gtirb

if platform.system() == "Linux":
    import lief

ex_dir = Path("./examples/")
ex_asm_dir = ex_dir / "asm_examples"


class LibrarySymbolsTests(unittest.TestCase):
    @unittest.skipUnless(
        platform.system() == "Linux", "This test is linux only."
    )
    def test_symbols_through_plt(self):
        """
        Test a library that calls local methods through
        the plt table and locally defined symbols
        do not point to proxy blocks.
        """

        library = "ex.so"
        with cd(ex_dir / "ex_lib_symbols"):
            self.assertTrue(compile("gcc", "g++", "-O0", []))
            self.assertTrue(disassemble(library, format="--ir")[0])

            ir_library = gtirb.IR.load_protobuf(library + ".gtirb")
            m = ir_library.modules[0]

            # foo is a symbol pointing to a code block
            foo = next(m.symbols_named("foo"))
            assert isinstance(foo.referent, gtirb.CodeBlock)

            # bar calls through the plt
            bar = next(m.symbols_named("bar"))
            bar_block = bar.referent
            callee = [
                e.target
                for e in bar_block.outgoing_edges
                if e.label.type == gtirb.Edge.Type.Call
            ][0]
            assert [s.name for s in m.sections_on(callee.address)][0] in [
                ".plt",
                ".plt.sec",
            ]


class IFuncSymbolsTests(unittest.TestCase):
    @unittest.skipUnless(
        platform.system() == "Linux", "This test is linux only."
    )
    def test_gnu_indirect_function(self):
        """
        Test a binary that calls a local method defined as
        gnu_indirect_function through plt and check if the local symbol is
        chosen over global symbols.
        """

        binary = "ex.so"
        with cd(ex_asm_dir / "ex_ifunc"):
            self.assertTrue(compile("gcc", "g++", "-O0", []))
            self.assertTrue(disassemble(binary, format="--asm")[0])
            self.assertTrue(
                reassemble(
                    "gcc",
                    binary,
                    extra_flags=[
                        "-shared",
                        "-Wl,--version-script=ex.map",
                        "-nostartfiles",
                    ],
                )
            )

            binlief = lief.parse(binary)
            for relocation in binlief.relocations:
                # The rewritten binary should not contain any JUMP_SLOT
                # relocation: the relocation for strcmp should be
                # R_X86_64_IRELATIVE instead of R_X86_64_JUMP_SLOT.
                self.assertTrue(
                    lief.ELF.RELOCATION_X86_64(relocation.type)
                    != lief.ELF.RELOCATION_X86_64.JUMP_SLOT
                )


class OverlappingInstructionTests(unittest.TestCase):
    def subtest_lock_cmpxchg(self, example: str):
        """
        Subtest body for test_lock_cmpxchg
        """
        binary = "ex"
        self.assertTrue(compile("gcc", "g++", "-O0", []))
        gtirb_file = "ex.gtirb"
        self.assertTrue(disassemble(binary, gtirb_file, format="--ir")[0])

        ir_library = gtirb.IR.load_protobuf(gtirb_file)
        m = ir_library.modules[0]

        main_sym = next(m.symbols_named("main"))
        main_block = main_sym.referent

        self.assertIsInstance(main_block, gtirb.CodeBlock)

        # find the lock cmpxchg instruction - ensure it exists and is
        # reachable from main
        block = main_block
        inst_prefix_op = b"\xf0\x48\x0f\xb1"
        fallthru_count = 0
        fallthru_max = 5
        blocks = [main_block]
        while block.contents[: len(inst_prefix_op)] != inst_prefix_op:
            if fallthru_count == fallthru_max:
                trace = " -> ".join([hex(b.address) for b in blocks])
                msg = "exceeded max fallthru searching for lock cmpxchg: {}"
                self.fail(msg.format(trace))
            try:
                block = next(
                    e
                    for e in block.outgoing_edges
                    if e.label.type == gtirb.Edge.Type.Fallthrough
                ).target
            except StopIteration:
                self.fail("lock cmpxchg is not a code block")

            self.assertIsInstance(block, gtirb.CodeBlock)
            blocks.append(block)
            fallthru_count += 1

        self.assertEqual(len(list(block.incoming_edges)), 1)

    @unittest.skipUnless(
        platform.system() == "Linux", "This test is linux only."
    )
    def test_lock_cmpxchg(self):
        """
        Test a binary that contains legitimate overlapping instructions:
        e.g., 0x0: lock cmpxchg
        At 0x0, lock cmpxchg
        At 0x1,      cmpxchg
        """
        examples = (
            "ex_overlapping_instruction",
            "ex_overlapping_instruction_2",
        )

        for example in examples:
            with self.subTest(example=example), cd(ex_asm_dir / example):
                self.subtest_lock_cmpxchg(example)


class AuxDataTests(unittest.TestCase):
    @unittest.skipUnless(
        platform.system() == "Linux", "This test is linux only."
    )
    def test_cfi_table(self):
        """
        Test that cfi directives are correctly generated.
        """

        binary = "ex"
        with cd(ex_asm_dir / "ex_cfi_directives"):
            self.assertTrue(compile("gcc", "g++", "-O0", []))
            self.assertTrue(disassemble(binary, format="--ir")[0])

            ir_library = gtirb.IR.load_protobuf(binary + ".gtirb")
            m = ir_library.modules[0]
            cfi = m.aux_data["cfiDirectives"].data
            # we simplify directives to make queries easier

            found = False
            for offset, directives in cfi.items():
                directive_names = [elem[0] for elem in directives]
                if ".cfi_remember_state" in directive_names:
                    found = True
                    # the directive is at the end of the  block
                    assert offset.element_id.size == offset.displacement
                    assert directive_names == [
                        ".cfi_remember_state",
                        ".cfi_restore_state",
                        ".cfi_endproc",
                    ]
                    break
            self.assertTrue(found)

    @unittest.skipUnless(
        platform.system() == "Linux", "This test is linux only."
    )
    def test_dyn_shared(self):
        """
        Test that binary types for DYN SHARED are correctly generated.
        """
        binary = "fun.so"
        with cd(ex_dir / "ex_dyn_library"):
            self.assertTrue(compile("gcc", "g++", "-O0", []))
            self.assertTrue(disassemble(binary, format="--ir")[0])

            ir_library = gtirb.IR.load_protobuf(binary + ".gtirb")
            m = ir_library.modules[0]
            dyn = m.aux_data["binaryType"].data

            self.assertIn("DYN", dyn)
            self.assertIn("SHARED", dyn)
            self.assertNotIn("PIE", dyn)

    @unittest.skipUnless(
        platform.system() == "Linux", "This test is linux only."
    )
    def test_dyn_pie(self):
        """
        Test that binary types for DYN PIE are correctly generated.
        """
        binary = "ex"
        with cd(ex_asm_dir / "ex_plt_nop"):
            self.assertTrue(compile("gcc", "g++", "-O0", []))
            self.assertTrue(disassemble(binary, format="--ir")[0])

            ir_library = gtirb.IR.load_protobuf(binary + ".gtirb")
            m = ir_library.modules[0]
            dyn = m.aux_data["binaryType"].data

            self.assertIn("DYN", dyn)
            self.assertIn("PIE", dyn)
            self.assertNotIn("SHARED", dyn)

    @unittest.skipUnless(
        platform.system() == "Linux", "This test is linux only."
    )
    def test_dyn_none(self):
        """
        Test that binary types for non-DYN are correctly generated.
        """
        binary = "ex"
        with cd(ex_asm_dir / "ex_moved_label"):
            self.assertTrue(compile("gcc", "g++", "-O0", []))
            self.assertTrue(disassemble(binary, format="--ir")[0])

            ir_library = gtirb.IR.load_protobuf(binary + ".gtirb")
            m = ir_library.modules[0]
            dyn = m.aux_data["binaryType"].data

            self.assertIn("EXEC", dyn)
            self.assertNotIn("DYN", dyn)
            self.assertNotIn("PIE", dyn)
            self.assertNotIn("SHARED", dyn)

    @unittest.skipUnless(
        platform.system() == "Linux", "This test is linux only."
    )
    def test_misaligned_fde(self):
        """
        Test that misaligned_fde_start is correctly generated.
        """
        binary = "ex"
        modes = [
            False,  # no strip
            True,  # strip
        ]

        for mode in modes:
            with self.subTest(mode=mode):
                with cd(ex_asm_dir / "ex_misaligned_fde"):
                    self.assertTrue(compile("gcc", "g++", "-O0", []))
                    self.assertTrue(
                        disassemble(binary, format="--ir", strip=mode)[0]
                    )

                    ir_library = gtirb.IR.load_protobuf(binary + ".gtirb")
                    m = ir_library.modules[0]

                    main_sym = next(m.symbols_named("main"))
                    main_block = main_sym.referent
                    outedges = [
                        edge
                        for edge in main_block.outgoing_edges
                        if edge.label.type == EdgeType.Fallthrough
                    ]
                    self.assertEqual(1, len(outedges))
                    block = outedges[0].target
                    # LEA should have a symbolic expression.
                    # If `bar` is not recognized as misaligned_fde_start,
                    # the LEA will be missing a symbolic expression.
                    self.assertTrue(
                        list(
                            m.symbolic_expressions_at(
                                range(
                                    block.address, block.address + block.size
                                )
                            )
                        )
                    )

    @unittest.skipUnless(
        platform.system() == "Linux", "This test is linux only."
    )
    def test_souffle_relations(self):
        """Test `--with-souffle-relations' equivalence to `--debug-dir'."""

        with cd(ex_dir / "ex1"):
            # build
            self.assertTrue(compile("gcc", "g++", "-O0", []))

            # disassemble
            if not os.path.exists("dbg"):
                os.mkdir("dbg")
            self.assertTrue(
                disassemble(
                    "ex",
                    format="--ir",
                    extra_args=[
                        "-F",
                        "--with-souffle-relations",
                        "--debug-dir",
                        "dbg",
                    ],
                )[0]
            )

            # load the gtirb
            ir = gtirb.IR.load_protobuf("ex.gtirb")
            m = ir.modules[0]

            # dump relations to directory
            if not os.path.exists("aux"):
                os.mkdir("aux")
            for table, ext in [
                ("souffleFacts", "facts"),
                ("souffleOutputs", "csv"),
            ]:
                for name, relation in m.aux_data[table].data.items():
                    dirname, filename = name.split(".", 1)
                    _, csv = relation
                    path = Path("aux", dirname, f"{filename}.{ext}")
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with open(path, "w") as out:
                        out.write(csv)

            # compare the relations directories
            subprocess.check_call(["diff", "dbg", "aux"])

    def assert_regex_match(self, text, pattern):
        """
        Like unittest's assertRegex, but also return the match object on
        success.

        assertRegex provides a nice output on failure, but doesn't return the
        match object, so we assert, and then search.
        """
        compiled = re.compile(pattern)
        self.assertRegex(text, compiled)
        return re.search(compiled, text)

    @unittest.skipUnless(
        platform.system() == "Linux", "This test is linux only."
    )
    def test_dynamic_init_fini(self):
        """
        Test generating auxdata from DT_INIT and DT_FINI dynamic entries
        """
        binary = "ex"
        with cd(ex_dir / "ex_dynamic_initfini"):
            self.assertTrue(compile("gcc", "g++", "-O0", []))

            # Ensure INIT / FINI are present (so that this breaks if compiler
            # behavior changes in the future)
            readelf = subprocess.run(
                ["readelf", "--dynamic", binary],
                check=True,
                capture_output=True,
                text=True,
            )
            template = r"0x[0-9a-f]+\s+\({}\)\s+(0x[0-9a-f]+)"
            init_match = self.assert_regex_match(
                readelf.stdout, template.format("INIT")
            )
            fini_match = self.assert_regex_match(
                readelf.stdout, template.format("FINI")
            )

            self.assertTrue(disassemble(binary, format="--ir")[0])

            ir = gtirb.IR.load_protobuf(binary + ".gtirb")
            m = ir.modules[0]
            init = m.aux_data["elfDynamicInit"].data
            fini = m.aux_data["elfDynamicFini"].data

            self.assertIsInstance(init, gtirb.CodeBlock)
            self.assertIsInstance(fini, gtirb.CodeBlock)

            self.assertEqual(int(init_match.group(1), 16), init.address)
            self.assertEqual(int(fini_match.group(1), 16), fini.address)


class RawGtirbTests(unittest.TestCase):
    @unittest.skipUnless(
        platform.system() == "Linux", "This test is linux only."
    )
    def test_read_gtirb(self):

        binary = "ex"
        with cd(ex_dir / "ex1"):
            self.assertTrue(compile("gcc", "g++", "-O0", []))

            # Output GTIRB file without disassembling.
            self.assertTrue(
                disassemble(
                    binary, format="--ir", extra_args=["--no-analysis"]
                )[0]
            )

            # Disassemble GTIRB input file.
            self.assertTrue(disassemble("ex.gtirb", format="--asm")[0])

            self.assertTrue(
                reassemble("gcc", "ex.gtirb", extra_flags=["-nostartfiles"])
            )
            self.assertTrue(test())


class DataDirectoryTests(unittest.TestCase):
    @unittest.skipUnless(
        platform.system() == "Windows", "This test is Windows only."
    )
    def test_data_directories_in_code(self):
        with cd(ex_dir / "ex1"):
            subprocess.run(make("clean"), stdout=subprocess.DEVNULL)

            # Compile with `.rdata' section merged to `.text'.
            proc = subprocess.run(
                ["cl", "/Od", "ex.c", "/link", "/merge:.rdata=.text"],
                stdout=subprocess.DEVNULL,
            )
            self.assertEqual(proc.returncode, 0)

            # Disassemble to GTIRB file.
            self.assertTrue(disassemble("ex.exe", format="--ir")[0])

            # Load the GTIRB file.
            ir = gtirb.IR.load_protobuf("ex.exe.gtirb")
            module = ir.modules[0]

            def is_code(section):
                return gtirb.ir.Section.Flag.Executable in section.flags

            pe_data_directories = module.aux_data["peDataDirectories"].data
            code_blocks = [
                (b.address, b.address + b.size) for b in module.code_blocks
            ]
            for _, addr, size in pe_data_directories:
                # Check data directories in code sections are data blocks.
                if size > 0:
                    if any(s for s in module.sections_on(addr) if is_code(s)):
                        data_block = next(module.data_blocks_on(addr), None)
                        self.assertIsNotNone(data_block)

                # Check no code blocks were created within data directories.
                for start, end in code_blocks:
                    self.assertFalse(start <= addr <= end)


class PeResourcesTests(unittest.TestCase):
    @unittest.skipUnless(
        platform.system() == "Windows", "This test is Windows only."
    )
    def test_generate_resources(self):
        with cd(ex_dir / "ex_rsrc"):
            # Build example with PE resource file.
            proc = subprocess.run(make("clean"), stdout=subprocess.DEVNULL)
            self.assertEqual(proc.returncode, 0)

            proc = subprocess.run(make("all"), stdout=subprocess.DEVNULL)
            self.assertEqual(proc.returncode, 0)

            # Disassemble to GTIRB file.
            self.assertTrue(
                disassemble(
                    "ex.exe",
                    format="--asm",
                    extra_args=[
                        "--generate-import-libs",
                        "--generate-resources",
                    ],
                )
            )

            # Reassemble with regenerated RES file.
            ml, entry = "ml64", "__EntryPoint"
            if os.environ.get("VSCMD_ARG_TGT_ARCH") == "x86":
                ml, entry = "ml", "_EntryPoint"
            self.assertTrue(
                reassemble(
                    ml,
                    "ex.exe",
                    extra_flags=[
                        "/link",
                        "ex.res",
                        "/entry:" + entry,
                        "/subsystem:console",
                    ],
                )
            )

            proc = subprocess.run(make("check"), stdout=subprocess.DEVNULL)
            self.assertEqual(proc.returncode, 0)


class SymbolSelectionTests(unittest.TestCase):
    def check_first_sym_expr(
        self, m: gtirb.Module, block_name: str, target_name: str
    ) -> None:
        """
        Check that the first Symexpr in a block identified
        with symbol 'block_name' points to a symbol with
        name 'target_name'
        """
        sym = next(m.symbols_named(block_name))
        self.assertIsInstance(sym.referent, gtirb.CodeBlock)
        block = sym.referent
        sexpr = sorted(
            [
                t[1:]
                for t in block.byte_interval.symbolic_expressions_at(
                    range(block.address, block.address + block.size)
                )
            ]
        )[0]
        self.assertEqual(sexpr[1].symbol.name, target_name)

    @unittest.skipUnless(
        platform.system() == "Linux", "This test is linux only."
    )
    def test_symbol_selection(self):
        """
        Test that the right symbols are chosen for relocations
        and for functions.
        """

        binary = "ex"
        with cd(ex_asm_dir / "ex_symbol_selection"):
            self.assertTrue(compile("gcc", "g++", "-O0", []))
            self.assertTrue(disassemble(binary, format="--ir")[0])

            ir_library = gtirb.IR.load_protobuf(binary + ".gtirb")
            m = ir_library.modules[0]

            self.check_first_sym_expr(m, "Block_hello", "hello_not_hidden")
            self.check_first_sym_expr(m, "Block_how", "how_global")
            self.check_first_sym_expr(m, "Block_bye", "bye_obj")

            # check symbols at the end of sections
            syms = []
            for s in [
                "__init_array_end",
                "end_of_data_section",
                "edata",
                "_end",
            ]:
                syms += m.symbols_named(s)
            self.assertTrue(all(s.at_end for s in syms))

            # check chosen function names
            fun_names = {
                sym.name for sym in m.aux_data["functionNames"].data.values()
            }
            self.assertIn("fun", fun_names)
            self.assertNotIn("_fun", fun_names)

    @unittest.skipUnless(
        platform.system() == "Linux", "This test is linux only."
    )
    def test_boundary_sym_expr(self):
        """
        Test that symexpr that should be pointing
        to the end of a section indeed points to
        the symbol at the end of the section.
        """

        binary = "ex"
        with cd(ex_asm_dir / "ex_boundary_sym_expr"):
            self.assertTrue(compile("gcc", "g++", "-O0", []))
            self.assertTrue(disassemble(binary, format="--ir")[0])
            ir_library = gtirb.IR.load_protobuf(binary + ".gtirb")
            m = ir_library.modules[0]
            self.check_first_sym_expr(m, "load_end", "nums_end")


class ElfSymbolAuxdataTests(unittest.TestCase):
    @unittest.skipUnless(
        platform.system() == "Linux", "This test is linux only."
    )
    def test_lib_symbol_versions(self):
        """
        Test that symbols have the right version.
        """

        binary = "libfoo.so"
        with cd(ex_dir / "ex_symver"):
            self.assertTrue(compile("gcc", "g++", "-O0", []))
            self.assertTrue(disassemble(binary, format="--ir")[0])

            ir_library = gtirb.IR.load_protobuf(binary + ".gtirb")
            m = ir_library.modules[0]

            (defs, needed, symver_entries) = m.aux_data[
                "elfSymbolVersions"
            ].data

            # The version of the library itself is recorded in defs
            # This is typically SymbolVersionId = 1 (but I am not sure if it's
            # required by the spec to be)
            VER_FLG_BASE = 0x1
            self.assertIn((["libfoo.so"], VER_FLG_BASE), defs.values())

            foo_symbols = sorted(
                m.symbols_named("foo"),
                key=lambda x: x.referent.address,
            )
            self.assertEqual(len(foo_symbols), 3)

            foo1, foo2, foo3 = foo_symbols
            # Symbols have the right versions
            self.assertEqual(
                defs[symver_entries[foo1][0]], (["LIBFOO_1.0"], 0)
            )
            self.assertEqual(
                defs[symver_entries[foo2][0]],
                (["LIBFOO_2.0", "LIBFOO_1.0"], 0),
            )
            self.assertEqual(
                defs[symver_entries[foo3][0]],
                (["LIBFOO_3.0", "LIBFOO_2.0"], 0),
            )

            # Check that foo@LIBFOO_1.0 and foo@LIBFOO_2.0 are not default
            self.assertTrue(symver_entries[foo1][1])
            self.assertTrue(symver_entries[foo2][1])
            self.assertFalse(symver_entries[foo3][1])

            bar_symbols = m.symbols_named("bar")

            bar1, bar2 = bar_symbols
            # Check needed symbol versions
            needed_versions = {
                needed["libbar.so"][symver_entries[bar1][0]],
                needed["libbar.so"][symver_entries[bar2][0]],
            }
            self.assertEqual(needed_versions, {"LIBBAR_1.0", "LIBBAR_2.0"})
            # Needed versions are not hidden
            self.assertFalse(symver_entries[bar1][1])
            self.assertFalse(symver_entries[bar2][1])

    @unittest.skipUnless(
        platform.system() == "Linux", "This test is linux only."
    )
    def test_copy_symbol_versions(self):
        def lookup_sym_ver_need(
            symbol: gtirb.Symbol,
        ) -> Optional[Tuple[str, str]]:
            """
            Get the library and version for a needed symbol
            """
            _, ver_needs, ver_entries = m.aux_data["elfSymbolVersions"].data

            ver_id, hidden = ver_entries[symbol]
            for lib, lib_ver_needs in ver_needs.items():
                if ver_id in lib_ver_needs:
                    return (lib, lib_ver_needs[ver_id])
                else:
                    raise KeyError(f"No ver need: {ver_id}")

        binary = "ex"
        with cd(ex_dir / "ex_copy_relo"):
            self.assertTrue(compile("gcc", "g++", "-O0", []))

            self.assertTrue(disassemble(binary, format="--ir")[0])

            ir_library = gtirb.IR.load_protobuf(binary + ".gtirb")
            m = ir_library.modules[0]

            # The proxy symbol should have an elfSymbolVersion entry
            sym_environ = next(m.symbols_named("__environ"))
            lib, version = lookup_sym_ver_need(sym_environ)

            self.assertRegex(lib, r"libc\.so\.\d+")
            self.assertRegex(version, r"GLIBC_[\d\.]+")

            sym_environ_copy = next(m.symbols_named("__environ_copy"))
            with self.assertRaises(KeyError, msg=str(sym_environ_copy)):
                lookup_sym_ver_need(sym_environ_copy)

            # Both the copy symbol and proxy symbol should have elfSymbolInfo
            elf_symbol_info = m.aux_data["elfSymbolInfo"].data

            self.assertEqual(
                elf_symbol_info[sym_environ][1:4],
                ("OBJECT", "GLOBAL", "DEFAULT"),
            )
            self.assertEqual(
                elf_symbol_info[sym_environ_copy][1:4],
                ("OBJECT", "GLOBAL", "DEFAULT"),
            )


class OverlayTests(unittest.TestCase):
    @unittest.skipUnless(
        platform.system() == "Windows", "This test is Windows only."
    )
    def test_pe_overlay(self):
        with cd(ex_dir / "ex1"):
            # Create binary with overlay data.
            proc = subprocess.run(make("clean"), stdout=subprocess.DEVNULL)
            self.assertEqual(proc.returncode, 0)

            proc = subprocess.run(make("all"), stdout=subprocess.DEVNULL)
            self.assertEqual(proc.returncode, 0)

            # Append bytes to the binary.
            with open("ex.exe", "a") as pe:
                pe.write("OVERLAY")

            # Disassemble to GTIRB file.
            self.assertTrue(disassemble("ex.exe", format="--ir")[0])

            # Check overlay aux data.
            ir = gtirb.IR.load_protobuf("ex.exe.gtirb")
            module = ir.modules[0]
            overlay = module.aux_data["overlay"].data
            self.assertEqual(bytes(overlay), b"OVERLAY")

    @unittest.skipUnless(
        platform.system() == "Linux", "This test is linux only."
    )
    def test_linux_overlay(self):
        with cd(ex_dir / "ex1"):
            # Create binary with overlay data.
            proc = subprocess.run(make("clean"), stdout=subprocess.DEVNULL)
            self.assertEqual(proc.returncode, 0)

            proc = subprocess.run(make("all"), stdout=subprocess.DEVNULL)
            self.assertEqual(proc.returncode, 0)

            # Append bytes to the binary.
            with open("ex", "a") as binary:
                binary.write("OVERLAY")

            # Disassemble to GTIRB file.
            self.assertTrue(disassemble("ex", format="--ir")[0])

            # Check overlay aux data.
            ir = gtirb.IR.load_protobuf("ex.gtirb")
            module = ir.modules[0]
            overlay = module.aux_data["overlay"].data
            self.assertEqual(bytes(overlay), b"OVERLAY")


class OutputTests(unittest.TestCase):
    def test_output_no_dir(self):
        """
        Writing output to a non-existent directory fails
        """
        output_types = (
            ("--ir", "out.gtirb"),
            ("--json", "out.json"),
            ("--asm", "out.s"),
        )

        ext = ".exe" if platform.system() == "Windows" else ""

        with cd(ex_dir / "ex1"):
            proc = subprocess.run(make("clean"), stdout=subprocess.DEVNULL)
            self.assertEqual(proc.returncode, 0)

            proc = subprocess.run(make("all"), stdout=subprocess.DEVNULL)
            self.assertEqual(proc.returncode, 0)

            for opt, filename in output_types:
                with self.subTest(opt=opt, filename=filename):
                    args = [
                        "ddisasm",
                        "ex" + ext,
                        opt,
                        os.path.join("nodir", filename),
                    ]
                    proc = subprocess.run(args, capture_output=True)

                    self.assertEqual(proc.returncode, 1)
                    self.assertIn(b"Error: failed to open file", proc.stderr)


class NpadTests(unittest.TestCase):
    @unittest.skipUnless(
        platform.system() == "Windows"
        and os.environ.get("VSCMD_ARG_TGT_ARCH") == "x86",
        "This test is Windows (x86) only.",
    )
    def test_npad_data_in_code(self):
        with cd(ex_asm_dir / "ex_npad"):
            subprocess.run(make("clean"), stdout=subprocess.DEVNULL)

            # Build assembly test case for all legacy npad macros.
            subprocess.run(make("all"), stdout=subprocess.DEVNULL)

            # Disassemble to GTIRB file.
            self.assertTrue(disassemble("ex.exe", format="--ir")[0])

            # Reassemble test case.
            proc = subprocess.run(
                ["gtirb-pprinter", "-b", "ex.exe", "ex.exe.gtirb"]
            )
            self.assertEqual(proc.returncode, 0)

            # Check reassembled outputs.
            self.assertTrue(test())

            # Load the GTIRB file and check padding.
            ir = gtirb.IR.load_protobuf("ex.exe.gtirb")
            module = ir.modules[0]
            table = module.aux_data["padding"].data
            padding = sorted(
                (k.element_id.address + k.displacement, v)
                for k, v in table.items()
            )
            sizes = [n for _, n in padding]
            self.assertEqual(sizes, list(range(1, 16)))


if __name__ == "__main__":
    unittest.main()
