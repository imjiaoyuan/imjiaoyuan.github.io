import os

def rename_files():
    # 定义重命名映射关系
    rename_map = {
        "230329-cis-acting-element-analysis.md": "230329-cis-element-analysis.md",
        "230422-use-hmmer-to-find.md": "230422-hmmer-homology-search.md", 
        "230424-intraspecies-collinearity-analysis.md": "230424-collinearity-analysis.md",
        "230501-installing-conda-on-linux.md": "230501-linux-conda-install.md",
        "230513-go-kegg-enrichment-analysis.md": "230513-enrichment-analysis.md",
        "230815-tbtools-quickly-completes-gene.md": "230815-tbtools-gene-annotation.md",
        "230815-wsl-builds-a-bioinformatics.md": "230815-wsl-bioinfo-setup.md",
        "230920-how-to-download-literature.md": "230920-download-papers.md",
        "230927-i-hope-you-ll-be.md": "230927-hope-and-freedom.md",
        "231002-implementing-a-rice-id.md": "231002-rice-id-converter.md"
    }

    # 获取当前目录下的所有文件
    files = os.listdir('.')

    # 遍历文件进行重命名
    for old_name in rename_map:
        if old_name in files:
            new_name = rename_map[old_name]
            try:
                os.rename(old_name, new_name)
                print(f"已重命名: {old_name} -> {new_name}")
            except Exception as e:
                print(f"重命名 {old_name} 时出错: {str(e)}")

if __name__ == "__main__":
    rename_files() 