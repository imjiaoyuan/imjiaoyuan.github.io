---
title: Projects
---

## Software

Some open-source software I develop and maintain.

- **recite**[typescript]: A no-framework English vocabulary trainer (DOM built by hand with a hyperscript helper, ~2k lines) running SM-2 spaced repetition across flashcard study, spelling practice, and listen-and-write dictation, where due reviews always queue ahead of the daily new-word cap and each list keeps its own progress. ［[blog](/9zgxm/), [github](https://github.com/imjiaoyuan/recite), [pages](https://jiaoyuan.org/recite/)］
- **jsrc**[python]: A bioinformatics CLI spanning sequence QC, genome and phylogeny analysis, gene regulatory networks, and computer-vision morphology (EFD shape descriptors), with lazy-loaded modules and a built-in background job manager. ［[blog](/4kcd2/), [github](https://github.com/imjiaoyuan/jsrc), [pypi](https://pypi.org/project/jsrc/)］
- **jkey**[python]: A pure-Python vault that fuses a password manager with a TOTP authenticator: import 2FA straight from QR images, encrypt any file, all under AES-256-CBC + HMAC-SHA256 with a 5-minute session cache. ［[blog](/7re93/), [github](https://github.com/imjiaoyuan/jkey), [pypi](https://pypi.org/project/jkey/)］
- **RSS**[python]: A serverless RSS aggregator: a scheduled GitHub Actions workflow fetches feeds with zero backend, trims to recent posts, and ships a static page. ［[github](https://github.com/imjiaoyuan/RSS), [pages](http://jiaoyuan.org/RSS/)］
- **books**[python]: An EPUB toolkit that turns books into a navigable static HTML bookshelf with reading-progress memory, plus utilities to slim bloated files, strip ads and fix metadata, and interactively edit chapter titles. ［[github](https://github.com/imjiaoyuan/books), [pages](http://jiaoyuan.org/books/)］
- **blog**[python]: A zero-dependency static site generator (~1.3k lines, stdlib only) with CRC24 short-hash URLs, KaTeX math, and no-JS-by-default rendering. ［[blog](/5xbok/), [github](https://github.com/imjiaoyuan/imjiaoyuan.github.io)］

## AUR Packages

The Arch User Repository (AUR) is a community-driven collection of PKGBUILD recipes that makepkg builds and pacman installs. Arch's low barrier to contribution has let me package a number of tools and libraries the official repos don't carry.

Packages I maintain:

- [autocycler-bin](https://aur.archlinux.org/packages/autocycler-bin): Tool for combining multiple long-read assemblies into a consensus
- [cgmlst-dists](https://aur.archlinux.org/packages/cgmlst-dists): Pairwise Hamming distance matrix from cgMLST allele call tables
- [deeptools](https://aur.archlinux.org/packages/deeptools): Tools to process and analyze deep sequencing data (ChIP-seq, ATAC-seq, RNA-seq, etc.)
- [foldcomp](https://aur.archlinux.org/packages/foldcomp): Compress and index protein structures with torsion angles
- [foldcomp-bin](https://aur.archlinux.org/packages/foldcomp-bin): Compress and index protein structures with torsion angles
- [folddisco-bin](https://aur.archlinux.org/packages/folddisco-bin): Fast indexing and search of discontinuous motifs in protein structures
- [foldmason-bin](https://aur.archlinux.org/packages/foldmason-bin): Multiple protein structure alignment at scale
- [foldseek](https://aur.archlinux.org/packages/foldseek): Fast and sensitive comparison of large protein structure sets
- [foldseek-bin](https://aur.archlinux.org/packages/foldseek-bin): Fast and sensitive comparison of large protein structure sets
- [igblast](https://aur.archlinux.org/packages/igblast): NCBI IgBLAST: immunoglobulin and T-cell receptor sequence annotation
- [iqtree-bin](https://aur.archlinux.org/packages/iqtree-bin): Efficient phylogenomic software by maximum likelihood
- [jcvi](https://aur.archlinux.org/packages/jcvi): Python utility libraries on genome assembly, annotation and comparative genomics
- [jkey](https://aur.archlinux.org/packages/jkey): Python library for password management and TOTP verification
- [jsrc](https://aur.archlinux.org/packages/jsrc): Python library for bioinformatics and scientific computing
- [lexicmap](https://aur.archlinux.org/packages/lexicmap): Efficient sequence alignment against millions of prokaryotic and viral genomes
- [lexicmap-bin](https://aur.archlinux.org/packages/lexicmap-bin): Efficient sequence alignment against millions of prokaryotic and viral genomes
- [magicblast](https://aur.archlinux.org/packages/magicblast): NCBI MagicBLAST: maps next-generation RNA/DNA reads to a genome or transcriptome
- [metabuli-bin](https://aur.archlinux.org/packages/metabuli-bin): Specific and sensitive metagenomic classification via joint amino acid and DNA k-mer analysis
- [minigraph](https://aur.archlinux.org/packages/minigraph): Pangenome graph construction and sequence-to-graph alignment tool
- [miniprot](https://aur.archlinux.org/packages/miniprot): Protein-to-genome aligner with high splicing (intron) accuracy
- [mlst](https://aur.archlinux.org/packages/mlst): Scan contig files against traditional PubMLST typing schemes
- [mmseqs2-bin](https://aur.archlinux.org/packages/mmseqs2-bin): Ultra fast and sensitive sequence search and clustering suite
- [modkit-bin](https://aur.archlinux.org/packages/modkit-bin): Bioinformatics tool for working with modified bases in BAM/CRAM files
- [oarfish-bin](https://aur.archlinux.org/packages/oarfish-bin): Suite of tools for working with long-read transcriptome data (RNA-seq) from PacBio and Oxford Nanopore
- [orffinder](https://aur.archlinux.org/packages/orffinder): NCBI ORFfinder: finds Open Reading Frames (ORFs) in a query sequence
- [paml-bin](https://aur.archlinux.org/packages/paml-bin): Phylogenetic analysis by maximum likelihood
- [pi-coding-agent](https://aur.archlinux.org/packages/pi-coding-agent): Coding agent CLI with read, bash, edit, write tools and session management
- [polypolish-bin](https://aur.archlinux.org/packages/polypolish-bin): Short-read polishing tool for bacterial genome assemblies
- [raxml-ng-bin](https://aur.archlinux.org/packages/raxml-ng-bin): Phylogenetic tree inference tool which uses maximum-likelihood (ML) optimality criterion
- [seqkit](https://aur.archlinux.org/packages/seqkit): Cross-platform and ultrafast toolkit for FASTA/Q file manipulation in Golang
- [seqkit-bin](https://aur.archlinux.org/packages/seqkit-bin): Cross-platform and ultrafast toolkit for FASTA/Q file manipulation in Golang
- [seqtk](https://aur.archlinux.org/packages/seqtk): Toolkit for processing sequences in FASTA/Q formats
- [snp-dists](https://aur.archlinux.org/packages/snp-dists): Pairwise SNP distance matrix from a FASTA multiple sequence alignment
- [strdust-bin](https://aur.archlinux.org/packages/strdust-bin): Tandem repeat genotyper for long reads
- [table2asn](https://aur.archlinux.org/packages/table2asn): NCBI tool that converts 5-column feature tables into ASN.1 for GenBank submission (successor to tbl2asn)
- [taxonkit](https://aur.archlinux.org/packages/taxonkit): Cross-platform and efficient toolkit for rapid taxonomic operations on BARCODE, ASV, OTU or any biological sequences with taxonomy annotation
- [taxonkit-bin](https://aur.archlinux.org/packages/taxonkit-bin): Cross-platform and efficient toolkit for rapid taxonomic operations on BARCODE, ASV, OTU or any biological sequences with taxonomy annotation
- [ucsc-bigbed-bin](https://aur.archlinux.org/packages/ucsc-bigbed-bin): UCSC bigBed format utilities: bedToBigBed, bigBedToBed, bigBedInfo
- [ucsc-bigwig-bin](https://aur.archlinux.org/packages/ucsc-bigwig-bin): UCSC bigWig format utilities: wigToBigWig, bedGraphToBigWig, bigWigToBedGraph, bigWigInfo, bigWigAverageOverBed, bigWigSummary, fetchChromSizes
- [ucsc-blat-bin](https://aur.archlinux.org/packages/ucsc-blat-bin): UCSC BLAT alignment suite: blat, gfServer, gfClient, isPcr
- [ucsc-genepred-bin](https://aur.archlinux.org/packages/ucsc-genepred-bin): UCSC genePred format converters: gtfToGenePred, genePredToGtf, gff3ToGenePred, genePredToBed, bedToGenePred
- [ucsc-liftover-bin](https://aur.archlinux.org/packages/ucsc-liftover-bin): UCSC liftOver: converts genome coordinates between assemblies
- [ucsc-psl-bin](https://aur.archlinux.org/packages/ucsc-psl-bin): UCSC PSL alignment utilities: pslToBed, pslReps, pslCDnaFilter
- [ucsc-twobit-bin](https://aur.archlinux.org/packages/ucsc-twobit-bin): UCSC twoBit genome format utilities: faToTwoBit, twoBitToFa, twoBitInfo
