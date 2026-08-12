---
title: Projects
---

Some open-source projects I develop and maintain.

- **recite**[typescript]: A no-framework English vocabulary trainer (DOM built by hand with a hyperscript helper, ~2k lines) running SM-2 spaced repetition across flashcard study, spelling practice, and listen-and-write dictation, where due reviews always queue ahead of the daily new-word cap and each list keeps its own progress. ［[blog](/9zgxm/), [github](https://github.com/imjiaoyuan/recite), [pages](https://jiaoyuan.org/recite/)］
- **jsrc**[python]: A bioinformatics CLI spanning sequence QC, genome and phylogeny analysis, gene regulatory networks, and computer-vision morphology (EFD shape descriptors), with lazy-loaded modules and a built-in background job manager. ［[blog](/4kcd2/), [github](https://github.com/imjiaoyuan/jsrc), [pypi](https://pypi.org/project/jsrc/)］
- **jkey**[python]: A pure-Python vault that fuses a password manager with a TOTP authenticator: import 2FA straight from QR images, encrypt any file, all under AES-256-CBC + HMAC-SHA256 with a 5-minute session cache. ［[blog](/7re93/), [github](https://github.com/imjiaoyuan/jkey), [pypi](https://pypi.org/project/jkey/)］
- **RSS**[python]: A serverless RSS aggregator: a scheduled GitHub Actions workflow fetches feeds with zero backend, trims to recent posts, and ships a static page. ［[github](https://github.com/imjiaoyuan/RSS), [pages](http://jiaoyuan.org/RSS/)］
- **books**[python]: An EPUB toolkit that turns books into a navigable static HTML bookshelf with reading-progress memory, plus utilities to slim bloated files, strip ads and fix metadata, and interactively edit chapter titles. ［[github](https://github.com/imjiaoyuan/books), [pages](http://jiaoyuan.org/books/)］
- **blog**[python]: A zero-dependency static site generator (~1.3k lines, stdlib only) with CRC24 short-hash URLs, KaTeX math, and no-JS-by-default rendering. ［[blog](/5xbok/), [github](https://github.com/imjiaoyuan/imjiaoyuan.github.io)］

## AUR

The Arch User Repository (AUR) is a community-driven repository for Arch Linux users. It contains package descriptions (PKGBUILDs) that allow you to compile a package from source with makepkg and then install it via pacman.

Packages I maintain:

- [taxonkit-bin](https://aur.archlinux.org/packages/taxonkit-bin): A practical and efficient NCBI Taxonomy toolkit in Go
- [lexicmap-bin](https://aur.archlinux.org/packages/lexicmap-bin): Efficient sequence alignment tool for querying nucleotide sequences against millions of prokaryotic genomes
- [table2asn](https://aur.archlinux.org/packages/table2asn): NCBI tool that converts 5-column feature tables into ASN.1 for GenBank submission (successor to tbl2asn)
- [deeptools](https://aur.archlinux.org/packages/deeptools): Tools to process and analyze deep sequencing data (ChIP-seq, ATAC-seq, RNA-seq, etc.)
- [python-jsrc](https://aur.archlinux.org/packages/python-jsrc): Python library for bioinformatics and scientific computing
- [python-jkey](https://aur.archlinux.org/packages/python-jkey): Python library for password management and TOTP verification
- [orffinder](https://aur.archlinux.org/packages/orffinder): NCBI ORFfinder: finds Open Reading Frames (ORFs) in a query sequence
- [magicblast](https://aur.archlinux.org/packages/magicblast): NCBI MagicBLAST: maps next-generation RNA/DNA reads to a genome or transcriptome
- [jcvi](https://aur.archlinux.org/packages/jcvi): Python utility libraries on genome assembly, annotation and comparative genomics
- [iqtree-bin](https://aur.archlinux.org/packages/iqtree-bin): Efficient phylogenomic software by maximum likelihood (precompiled binary) https://doi.org/10.1093/molbev/msaa015
- [igblast](https://aur.archlinux.org/packages/igblast): NCBI IgBLAST: immunoglobulin and T-cell receptor sequence annotation
