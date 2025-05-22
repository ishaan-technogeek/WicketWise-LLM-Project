class SchemaCleaningAgent:
    def clean_schema(self, dataset_info: dict) -> dict:
        # dataset_info: {selected_tables: [...], relevant_fields: {...}}
        cleaned = {
          "tables": [t.strip().lower() for t in dataset_info["selected_tables"]],
          "fields": {
            t.strip().lower(): [c.strip().lower()
                                for c in cols]
            for t, cols in dataset_info["relevant_fields"].items()
          }
        }
        return cleaned

    def _normalize_name(self, name):
        """
        Helper method to apply normalization rules to a single name.
        Placeholder implementation.
        """
        # Example: convert to lowercase and replace spaces with underscores
        return name.lower().replace(" ", "_")
