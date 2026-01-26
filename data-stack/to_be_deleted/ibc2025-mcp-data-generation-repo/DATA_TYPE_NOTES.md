# Data Type Considerations for Glue Tables

## Important Notes on Data Types

### Nullable Integer Fields
When generating synthetic data with pandas and saving to Parquet format, integer fields that contain `None` values are automatically converted to `float64` (double) type to accommodate NaN values. This is a limitation of how pandas handles nullable integers in Parquet files.

### Affected Fields

#### Titles Table
- **season_number**: Set to `None` for movies and documentaries (only series have season numbers)
  - Glue type: `double` (not `int`)
- **episode_number**: Set to `None` for movies and documentaries (only series have episode numbers)
  - Glue type: `double` (not `int`)

#### Customers Table
- **subscription_end_date**: Set to `None` for active customers
  - Glue type: `timestamp` (handles nulls correctly)

### Why This Matters
If the Glue table schema defines these fields as `int`, Athena queries will fail with:
```
HIVE_BAD_DATA: Malformed Parquet file. Field season_number's type DOUBLE in parquet file 
is incompatible with type integer defined in table schema
```

### Solution
The CDK code has been updated to define these nullable integer fields as `double` type in the Glue catalog to match the actual Parquet file schema.

### Future Considerations
If you need true integer types with null support, consider:
1. Using PyArrow's nullable integer types (requires PyArrow 1.0+)
2. Using a sentinel value (e.g., -1) instead of None
3. Storing these fields as strings and converting in queries
4. Using separate boolean flags to indicate null values

## Testing After Deployment
After deploying the CDK stacks, verify the data types are correct:

```sql
-- Test query that should work without errors
SELECT 
    title_type,
    COUNT(*) as count,
    AVG(season_number) as avg_season,  -- Will be NULL for movies/documentaries
    AVG(episode_number) as avg_episode  -- Will be NULL for movies/documentaries
FROM acme_streaming_data.titles
GROUP BY title_type;
```