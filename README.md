# Appli streamlit pour découvrir les outils du serveur MCP datagouv

Github du MCP data gouv : https://github.com/datagouv/datagouv-mcp

## Initialisation de l'environnement avec UV

```bash
$ uv venv
$ source .venv/bin/activate # source .venv/scripts/activate
$ uv sync
```

## Lancement 

```bash
$ streamlit run main.py
```

## Note pour le workflow du MCP


Note: Recommended workflow: 

1) Use search_datasets to find the dataset,
2) Use list_dataset_resources to see available resources,
3) Use query_resource_data with default page_size (20) to preview data structure.

For small datasets (<500 rows), increase page_size or paginate. For large datasets (>1000 rows), use download_and_parse_resource instead. Works for CSV/XLS resources within Tabular API size limits (CSV ≤ 100 MB, XLSX ≤ 12.5 MB).
